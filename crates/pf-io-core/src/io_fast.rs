//! Fast readers that produce Arrow IPC stream bytes.
//!
//! These functions read data using Rust (parquet/csv), then serialize to
//! Arrow IPC stream so Python can reconstruct a pyarrow.Table without copies.

use crate::error::{IoError, Result};
use arrow::datatypes::SchemaRef;
use arrow::ipc::writer::StreamWriter;
use arrow::record_batch::RecordBatch;
use parquet::arrow::ProjectionMask;
use std::fs::File;
use std::path::Path;

/// Read a Parquet file and return Arrow IPC stream bytes with optional projection and row-group selection.
pub fn read_parquet_ipc<P: AsRef<Path>>(
    path: P,
    columns: Option<&[String]>,
    row_groups: Option<&[usize]>,
    batch_size: Option<usize>,
) -> Result<Vec<u8>> {
    let path_ref = path.as_ref();
    if !path_ref.exists() {
        return Err(IoError::FileNotFound(path_ref.display().to_string()));
    }

    // Open Parquet file
    let file = File::open(path_ref)?;

    // Use parquet->arrow RecordBatch reader (Arrow/Parquet 57 API expects a ChunkReader, e.g., File)
    let mut builder = parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|e| IoError::Other(e.to_string()))?;

    // Row-group selection
    if let Some(rgs) = row_groups {
        builder = builder.with_row_groups(rgs.to_vec());
    }

    // Column projection by name -> indices using ProjectionMask
    if let Some(cols) = columns {
        let meta = builder.metadata();
        let schema = meta.file_metadata().schema_descr();
        // Map names to leaf column indices in schema descriptor
        // If a name is not found, ignore silently (could also error)
        let mut leaves: Vec<usize> = Vec::new();
        for name in cols {
            for i in 0..schema.num_columns() {
                if schema.column(i).name() == name {
                    leaves.push(i);
                    break;
                }
            }
        }
        if !leaves.is_empty() {
            let mask = ProjectionMask::leaves(schema, leaves);
            builder = builder.with_projection(mask);
        }
    }

    if let Some(bs) = batch_size {
        builder = builder.with_batch_size(bs);
    }

    let rb_reader = builder.build().map_err(|e| IoError::Other(e.to_string()))?;

    // Collect batches
    let mut batches: Vec<RecordBatch> = Vec::new();
    for maybe_batch in rb_reader {
        let batch = maybe_batch.map_err(|e| IoError::Other(e.to_string()))?;
        batches.push(batch);
    }

    // Determine schema
    let schema: SchemaRef = match batches.first() {
        Some(b) => b.schema(),
        None => {
            let empty = arrow::datatypes::Schema::empty();
            std::sync::Arc::new(empty)
        }
    };

    // Serialize to Arrow IPC stream
    let mut buffer = Vec::<u8>::new();
    {
        let mut writer = StreamWriter::try_new(&mut buffer, &schema)
            .map_err(|e| IoError::Other(e.to_string()))?;
        for b in batches {
            writer.write(&b).map_err(|e| IoError::Other(e.to_string()))?;
        }
        writer.finish().map_err(|e| IoError::Other(e.to_string()))?;
    }

    Ok(buffer)
}

/// Read a CSV file and return Arrow IPC stream bytes.
/// Note: CSV fast-path temporarily disabled due to Arrow 57 API changes. Use Python path.
pub fn read_csv_ipc<P: AsRef<Path>>(
    _path: P,
    _delimiter: u8,
    _has_header: bool,
    _infer_schema: bool,
    _batch_size: Option<usize>,
) -> Result<Vec<u8>> {
    Err(IoError::Other(
        "CSV fast-path is temporarily unavailable on Arrow 57; falling back to Python reader is recommended".to_string(),
    ))
}
