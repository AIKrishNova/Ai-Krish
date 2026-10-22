import unittest

from assistant.ui import orb_math as om


class OrbMathTests(unittest.TestCase):
    def test_breathing_stays_in_range(self):
        values = [om.breathing_scale(i / 20.0) for i in range(100)]
        self.assertGreaterEqual(min(values), 0.95 - 1e-9)
        self.assertLessEqual(max(values), 1.05 + 1e-9)

    def test_listening_scale_follows_level_and_clamps(self):
        self.assertLess(om.listening_scale(0.0), om.listening_scale(1.0))
        self.assertEqual(om.listening_scale(5.0), om.listening_scale(1.0))
        self.assertEqual(om.listening_scale(-1.0), om.listening_scale(0.0))

    def test_rings_are_staggered_and_fade_out(self):
        starts = {round(om.ring_progress(0.0, i), 3) for i in range(3)}
        self.assertEqual(len(starts), 3)
        near, far = om.ring_look(0.1), om.ring_look(0.9)
        self.assertGreater(far[0], near[0])
        self.assertLess(far[1], near[1])

    def test_eight_particles_on_the_circle(self):
        points = om.particle_positions(1.0, count=8, radius=2.0)
        self.assertEqual(len(points), 8)
        for x, y in points:
            self.assertAlmostEqual((x * x + y * y) ** 0.5, 2.0, places=6)

    def test_five_bars_in_range(self):
        heights = om.bar_heights(0.7, 5)
        self.assertEqual(len(heights), 5)
        self.assertTrue(all(0.3 - 1e-9 <= v <= 1.0 + 1e-9 for v in heights))

    def test_shake_stops_after_duration(self):
        self.assertEqual(om.shake_offset(0.6), 0.0)
        self.assertEqual(om.shake_offset(-1.0), 0.0)
        self.assertTrue(all(abs(om.shake_offset(i / 100.0)) <= 8.0 for i in range(50)))

    def test_hue_shift_is_bounded(self):
        self.assertTrue(all(abs(om.hue_shift(i / 10.0)) <= 40.0 + 1e-9 for i in range(100)))


if __name__ == "__main__":
    unittest.main()
