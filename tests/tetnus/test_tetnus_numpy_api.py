import unittest

import parquetframe.tetnus.numpy as pfn
from parquetframe.tetnus import Tensor


class TestTetnusNumpyApi(unittest.TestCase):
    def test_creation(self):
        a = pfn.zeros((2, 3))
        self.assertEqual(a.shape, (2, 3))
        self.assertIsInstance(a, Tensor)

        b = pfn.ones((3, 2))
        self.assertEqual(b.shape, (3, 2))

        c = pfn.eye(3)
        self.assertEqual(c.shape, (3, 3))

        d = pfn.arange(0, 10, 2)
        self.assertEqual(d.shape, (5,))

        e = pfn.linspace(0, 1, 11)
        self.assertEqual(e.shape, (11,))

        f = pfn.full((2, 2), 7)
        self.assertEqual(f.shape, (2, 2))
        # Check value if possible, e.g. f.sum() should be 28
        val = f.sum().data()
        self.assertAlmostEqual(val[0] if isinstance(val, list) else val, 28.0)

    def test_operations(self):
        a = pfn.ones((2, 3))
        b = pfn.ones((3, 2))
        c = pfn.matmul(a, b)
        self.assertEqual(c.shape, (2, 2))

        d = pfn.add(a, a)
        self.assertEqual(d.shape, (2, 3))

        e = pfn.reshape(a, (3, 2))
        self.assertEqual(e.shape, (3, 2))

        f = pfn.transpose(a)
        self.assertEqual(f.shape, (3, 2))

        # Test method
        f2 = a.transpose()
        self.assertEqual(f2.shape, (3, 2))

        g = pfn.sum(a)
        val = g.data()
        self.assertAlmostEqual(val[0] if isinstance(val, list) else val, 6.0)

    def test_elementwise(self):
        a = pfn.zeros((2, 2))
        b = pfn.exp(a)  # exp(0) = 1
        val_b = b.sum().data()
        self.assertAlmostEqual(val_b[0] if isinstance(val_b, list) else val_b, 4.0)

        c = pfn.sin(a)  # sin(0) = 0
        val_c = c.sum().data()
        self.assertAlmostEqual(val_c[0] if isinstance(val_c, list) else val_c, 0.0)


if __name__ == "__main__":
    unittest.main()
