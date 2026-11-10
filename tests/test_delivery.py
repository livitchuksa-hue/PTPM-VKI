import sys
import os
import unittest
import datetime
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from Delivery import calculate_delivery_cost

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class TestDeliveryValidation(unittest.TestCase):

    def test_weight_below_minimum_returns_error(self):
        logging.info("Запуск: test_weight_below_minimum_returns_error")
        cost, date = calculate_delivery_cost(0.05, 100, "обычный")
        self.assertEqual(cost, -1)

    def test_weight_above_maximum_returns_error(self):
        logging.info("Запуск: test_weight_above_maximum_returns_error")
        cost, date = calculate_delivery_cost(51.0, 100, "обычный")
        self.assertEqual(cost, -1)

    def test_distance_below_one_returns_error(self):
        logging.info("Запуск: test_distance_below_one_returns_error")
        cost, date = calculate_delivery_cost(1.0, 0, "обычный")
        self.assertEqual(cost, -1)

    def test_distance_above_five_thousand_returns_error(self):
        logging.info("Запуск: test_distance_above_five_thousand_returns_error")
        cost, date = calculate_delivery_cost(1.0, 5001, "обычный")
        self.assertEqual(cost, -1)

    def test_unknown_package_type_returns_error(self):
        logging.info("Запуск: test_unknown_package_type_returns_error")
        cost, date = calculate_delivery_cost(1.0, 100, "стеклянный")
        self.assertEqual(cost, -1)

    def test_error_date_is_zero_string(self):
        logging.info("Запуск: test_error_date_is_zero_string")
        cost, date = calculate_delivery_cost(-1, 100, "обычный")
        self.assertEqual(date, "0000-00-00")


class TestDeliveryCost(unittest.TestCase):

    def test_base_cost_without_coefficients(self):
        logging.info("Запуск: test_base_cost_without_coefficients")
        cost, _ = calculate_delivery_cost(1.0, 100, "обычный")
        self.assertEqual(cost, 700)

    def test_weight_exactly_five_gets_low_weight_coefficient(self):
        logging.info("Запуск: test_weight_exactly_five_gets_low_weight_coefficient")
        cost, _ = calculate_delivery_cost(5.0, 100, "обычный")
        self.assertEqual(cost, 840)

    def test_weight_ten_gets_medium_coefficient(self):
        logging.info("Запуск: test_weight_ten_gets_medium_coefficient")
        cost, _ = calculate_delivery_cost(10.0, 100, "обычный")
        self.assertEqual(cost, 840)

    def test_weight_twenty_gets_high_coefficient(self):
        logging.info("Запуск: test_weight_twenty_gets_high_coefficient")
        cost, _ = calculate_delivery_cost(20.0, 100, "обычный")
        self.assertEqual(cost, 1050)

    def test_fragile_package_adds_surcharge(self):
        logging.info("Запуск: test_fragile_package_adds_surcharge")
        cost, _ = calculate_delivery_cost(1.0, 100, "хрупкий")
        self.assertEqual(cost, 1000)

    def test_dangerous_package_adds_surcharge(self):
        logging.info("Запуск: test_dangerous_package_adds_surcharge")
        cost, _ = calculate_delivery_cost(1.0, 100, "опасный")
        self.assertEqual(cost, 1700)

    def test_express_increases_total_cost(self):
        logging.info("Запуск: test_express_increases_total_cost")
        normal, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=False)
        express, _ = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        self.assertGreater(express, normal)


class TestDeliveryDate(unittest.TestCase):

    def test_short_distance_delivers_next_day(self):
        logging.info("Запуск: test_short_distance_delivers_next_day")
        _, date = calculate_delivery_cost(1.0, 100, "обычный")
        self.assertEqual(date, "2026-09-04")

    def test_distance_500_takes_one_day(self):
        logging.info("Запуск: test_distance_500_takes_one_day")
        _, date = calculate_delivery_cost(1.0, 500, "обычный")
        self.assertEqual(date, "2026-09-04")

    def test_distance_1000_takes_two_days(self):
        logging.info("Запуск: test_distance_1000_takes_two_days")
        _, date = calculate_delivery_cost(1.0, 1000, "обычный")
        self.assertEqual(date, "2026-09-05")

    def test_distance_501_rounds_up_to_two_days(self):
        logging.info("Запуск: test_distance_501_rounds_up_to_two_days")
        _, date = calculate_delivery_cost(1.0, 501, "обычный")
        self.assertEqual(date, "2026-09-05")

    def test_express_shortens_delivery_time(self):
        logging.info("Запуск: test_express_shortens_delivery_time")
        _, normal = calculate_delivery_cost(1.0, 2000, "обычный", is_express=False)
        _, express = calculate_delivery_cost(1.0, 2000, "обычный", is_express=True)
        self.assertLess(express, normal)

    def test_express_never_delivers_same_day(self):
        logging.info("Запуск: test_express_never_delivers_same_day")
        _, date = calculate_delivery_cost(1.0, 100, "обычный", is_express=True)
        send_date = datetime.date(2026, 9, 3)
        deliver_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        self.assertGreaterEqual((deliver_date - send_date).days, 1)


if __name__ == "__main__":
    unittest.main()