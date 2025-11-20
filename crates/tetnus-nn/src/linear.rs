use crate::module::Module;
use crate::{Result, TetnusNnError};
use tetnus_core::{Tensor, ops};
use tetnus_core::ops::Op;

/// A fully connected linear layer: y = xA^T + b
pub struct Linear {
    weight: Tensor,
    bias: Option<Tensor>,
}

impl Linear {
    /// Create a new Linear layer.
    ///
    /// # Arguments
    /// * `in_features` - Size of each input sample
    /// * `out_features` - Size of each output sample
    /// * `bias` - If set to false, the layer will not learn an additive bias.
    pub fn new(in_features: usize, out_features: usize, bias: bool) -> Result<Self> {
        // Kaiming initialization or similar would be better, but using randn for now
        let weight = Tensor::randn(vec![out_features, in_features])?;

        let bias_tensor = if bias {
            Some(Tensor::zeros(vec![out_features])?)
        } else {
            None
        };

        Ok(Linear {
            weight,
            bias: bias_tensor,
        })
    }
}

impl Module for Linear {
    fn forward(&self, input: &Tensor) -> Result<Tensor> {
        // y = input @ weight.T + bias

        // Transpose weight: [Out, In] -> [In, Out]
        let transpose_op = ops::view::TransposeOp::new(self.weight.shape().to_vec());
        let w_t = transpose_op.forward(&[&self.weight])?;

        // Matmul
        let mut output = ops::matmul::matmul(input, &w_t)?;

        if let Some(b) = &self.bias {
            // Broadcast add
            // Current tetnus-core::add requires exact shape match.
            // We manually broadcast bias [Out] -> [Batch, Out]
            let batch_size = output.shape()[0];
            let out_features = output.shape()[1];

            if b.shape()[0] != out_features {
                 return Err(TetnusNnError::InvalidInput(format!(
                    "Bias shape {:?} does not match output features {}",
                    b.shape(), out_features
                )));
            }

            // Create expanded bias
            // TODO: Optimize with true broadcasting in tetnus-core
            let bias_data = b.data();
            let expanded_data: Vec<f32> = (0..batch_size)
                .flat_map(|_| bias_data.iter().cloned())
                .collect();

            let bias_broadcast = Tensor::new(expanded_data, vec![batch_size, out_features])?;

            output = ops::elementwise::add(&output, &bias_broadcast)?;
        }

        Ok(output)
    }

    fn parameters(&self) -> Vec<Tensor> {
        let mut params = vec![self.weight.clone()];
        if let Some(b) = &self.bias {
            params.push(b.clone());
        }
        params
    }
}
