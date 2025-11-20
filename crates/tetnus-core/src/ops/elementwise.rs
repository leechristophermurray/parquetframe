/// Element-wise operations

use crate::{Tensor, Result, TetnusError, ops::Op};
use crate::kernels::cpu;
use std::sync::Arc;

pub struct AddOp;

impl Op for AddOp {
    fn forward(&self, inputs: &[&Tensor]) -> Result<Tensor> {
        if inputs.len() != 2 {
            return Err(TetnusError::InvalidOperation(
                "Add requires exactly 2 inputs".to_string()
            ));
        }

        let a = inputs[0];
        let b = inputs[1];

        // Check shapes match
        if a.shape() != b.shape() {
            return Err(TetnusError::ShapeMismatch {
                expected: a.shape().to_vec(),
                actual: b.shape().to_vec(),
            });
        }

        let a_data = a.data();
        let b_data = b.data();
        let mut c_data = vec![0.0; a.numel()];

        cpu::cpu_add(&a_data, &b_data, &mut c_data);

        Tensor::new(c_data, a.shape().to_vec())
    }

    fn backward(&self, grad_output: &Tensor) -> Result<Vec<Tensor>> {
        // For C = A + B:
        // dL/dA = dL/dC (gradient flows equally)
        // dL/dB = dL/dC
        Ok(vec![grad_output.clone(), grad_output.clone()])
    }

    fn name(&self) -> &str {
        "add"
    }
}

pub struct MulOp {
    // Store inputs for backward pass
    a: Tensor,
    b: Tensor,
}

impl MulOp {
    pub fn new(a: &Tensor, b: &Tensor) -> Self {
        Self {
            a: a.clone(),
            b: b.clone(),
        }
    }
}

impl Op for MulOp {
    fn forward(&self, inputs: &[&Tensor]) -> Result<Tensor> {
        if inputs.len() != 2 {
            return Err(TetnusError::InvalidOperation(
                "Mul requires exactly 2 inputs".to_string()
            ));
        }

        let a = inputs[0];
        let b = inputs[1];

        if a.shape() != b.shape() {
            return Err(TetnusError::ShapeMismatch {
                expected: a.shape().to_vec(),
                actual: b.shape().to_vec(),
            });
        }

        let a_data = a.data();
        let b_data = b.data();
        let mut c_data = vec![0.0; a.numel()];

        cpu::cpu_mul(&a_data, &b_data, &mut c_data);

        Tensor::new(c_data, a.shape().to_vec())
    }

    fn backward(&self, grad_output: &Tensor) -> Result<Vec<Tensor>> {
        // For C = A * B:
        // dL/dA = dL/dC * B
        // dL/dB = dL/dC * A
        let grad_a_data = grad_output.data();
        let b_data = self.b.data();
        let mut grad_a = vec![0.0; grad_a_data.len()];
        cpu::cpu_mul(&grad_a_data, &b_data, &mut grad_a);

        let a_data = self.a.data();
        let mut grad_b = vec![0.0; grad_a_data.len()];
        cpu::cpu_mul(&grad_a_data, &a_data, &mut grad_b);

        Ok(vec![
            Tensor::new(grad_a, self.a.shape().to_vec())?,
            Tensor::new(grad_b, self.b.shape().to_vec())?,
        ])
    }

    fn name(&self) -> &str {
        "mul"
    }
}

/// Helper functions
pub fn add(a: &Tensor, b: &Tensor) -> Result<Tensor> {
    let op = AddOp;
    let result = op.forward(&[a, b])?;

    if a.0.requires_grad || b.0.requires_grad {
        let internal = &*result.0;
        Ok(Tensor(Arc::new(crate::tensor::TensorInternal {
            data: Arc::clone(&internal.data),
            shape: internal.shape.clone(),
            strides: internal.strides.clone(),
            offset: internal.offset,
            device: internal.device,
            requires_grad: true,
            grad: parking_lot::Mutex::new(None),
            op: Some(Arc::new(op)),
            inputs: vec![a.clone(), b.clone()],
        })))
    } else {
        Ok(result)
    }
}

pub fn mul(a: &Tensor, b: &Tensor) -> Result<Tensor> {
    let op = MulOp::new(a, b);
    let result = op.forward(&[a, b])?;

    if a.0.requires_grad || b.0.requires_grad {
        let internal = &*result.0;
        Ok(Tensor(Arc::new(crate::tensor::TensorInternal {
            data: Arc::clone(&internal.data),
            shape: internal.shape.clone(),
            strides: internal.strides.clone(),
            offset: internal.offset,
            device: internal.device,
            requires_grad: true,
            grad: parking_lot::Mutex::new(None),
            op: Some(Arc::new(op)),
            inputs: vec![a.clone(), b.clone()],
        })))
    } else {
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        let a = Tensor::new(vec![1.0, 2.0, 3.0], vec![3]).unwrap();
        let b = Tensor::new(vec![4.0, 5.0, 6.0], vec![3]).unwrap();

        let c = add(&a, &b).unwrap();

        assert_eq!(c.data(), vec![5.0, 7.0, 9.0]);
    }

    #[test]
    fn test_mul() {
        let a = Tensor::new(vec![2.0, 3.0, 4.0], vec![3]).unwrap();
        let b = Tensor::new(vec![5.0, 6.0, 7.0], vec![3]).unwrap();

        let c = mul(&a, &b).unwrap();

        assert_eq!(c.data(), vec![10.0, 18.0, 28.0]);
    }
}
