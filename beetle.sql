-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 15, 2020 at 08:54 PM
-- Server version: 10.3.22-MariaDB-0+deb10u1
-- PHP Version: 7.3.19-1~deb10u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `beetle`
--

-- --------------------------------------------------------

--
-- Table structure for table `bms`
--

CREATE TABLE `bms` (
  `id` int(11) NOT NULL,
  `ts` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `cg` tinyint(4) NOT NULL,
  `t` float NOT NULL,
  `t_av` float NOT NULL,
  `v` float NOT NULL,
  `v_av` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=COMPACT;

--
-- Dumping data for table `bms`
--

INSERT INTO `bms` (`id`, `ts`, `cg`, `t`, `t_av`, `v`, `v_av`) VALUES
(1, '2020-08-16 01:54:28', 1, 35.6, 35.6, 7.801, 7.801),
(2, '2020-08-16 01:54:28', 2, 36.9, 36.9, 7.8, 7.8),
(3, '2020-08-16 01:54:28', 3, 37.1, 37.1, 7.79, 7.79),
(4, '2020-08-16 01:54:28', 4, 35.9, 35.8, 7.787, 7.787),
(5, '2020-08-16 01:54:28', 5, 39.4, 39.1, 7.786, 7.786),
(6, '2020-08-16 01:54:28', 6, 36.6, 36.6, 7.784, 7.784),
(7, '2020-08-16 01:54:28', 7, 36.5, 36.5, 7.784, 7.784),
(8, '2020-08-16 01:54:26', 9, 36.6, 36.4, 7.787, 7.787),
(9, '2020-08-16 01:54:26', 10, 37.4, 37.4, 7.778, 7.778),
(10, '2020-08-16 01:54:26', 11, 38.3, 37, 7.762, 7.762),
(11, '2020-08-16 01:54:26', 12, 39.2, 38.8, 7.734, 7.734),
(12, '2020-08-16 01:54:26', 13, 38.8, 39.5, 7.72, 7.72),
(13, '2020-08-16 01:54:26', 14, 37.9, 37.8, 7.714, 7.714),
(14, '2020-08-16 01:54:26', 15, 39, 39, 7.703, 7.703),
(15, '2020-08-16 01:54:26', 16, 36, 36, 7.712, 7.712);

-- --------------------------------------------------------

--
-- Table structure for table `history`
--

CREATE TABLE `history` (
  `id` int(11) NOT NULL,
  `ts` timestamp NOT NULL DEFAULT current_timestamp(),
  `front_t_av` float NOT NULL,
  `back_t_av` float NOT NULL,
  `v` float NOT NULL,
  `v_av` float NOT NULL,
  `v_min` float NOT NULL,
  `v_max` float NOT NULL,
  `amps` float NOT NULL,
  `charge_wh` float NOT NULL,
  `speed` float NOT NULL,
  `lat` float NOT NULL,
  `lon` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `state`
--

CREATE TABLE `state` (
  `id` int(11) NOT NULL,
  `ts` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `timeout` float NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `state`
--

INSERT INTO `state` (`id`, `ts`, `name`, `value`, `timeout`) VALUES
(1, '2020-08-11 13:37:35', 'charger', 'disabled', 0),
(3, '2020-08-16 01:54:26', 'ac_present', '1', 60),
(4, '2020-08-16 01:54:26', 'ignition', '0', 60),
(5, '2020-08-16 01:54:26', 'charging', '0', 60),
(6, '2020-08-16 01:54:28', 'front_t_av', '36.86', 60),
(7, '2020-08-16 01:54:28', 'back_t_av', '37.91', 60),
(8, '2020-08-16 01:54:28', 'v', '116.44', 60),
(9, '2020-08-16 01:54:28', 'v_av', '7.76', 60),
(10, '2020-08-16 01:54:28', 'v_min', '7.70', 60),
(11, '2020-08-16 01:54:26', 'v_max', '7.80', 60),
(12, '2020-08-16 01:54:28', 'front_polling_period', '1.68', 0),
(13, '2020-08-16 01:54:26', 'back_polling_period', '1.76', 0),
(14, '2020-08-16 00:00:14', 'trip_odometer', '2.5', 0),
(15, '2020-08-16 00:00:14', 'charge_odometer', '2.5', 0),
(16, '2020-08-15 22:30:35', 'heat_on_c', '23.0', 0),
(17, '2020-08-15 22:30:44', 'heat_off_c', '24.0', 0),
(18, '2020-08-16 01:54:28', 'speed', '0.0', 0),
(19, '2020-08-16 00:22:47', 'controller_temp', '0.0', 60),
(20, '2020-08-16 00:26:14', 'charge_wh', '0.0', 0),
(21, '2020-08-16 00:40:47', 'amps', '0.0', 0),
(22, '2020-08-16 01:11:17', 'wifi', 'always', 0),
(23, '2020-08-16 01:54:28', 'lat', '45.017339', 0),
(24, '2020-08-16 01:54:28', 'lon', '-93.355275500', 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bms`
--
ALTER TABLE `bms`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `history`
--
ALTER TABLE `history`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `state`
--
ALTER TABLE `state`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bms`
--
ALTER TABLE `bms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;
--
-- AUTO_INCREMENT for table `history`
--
ALTER TABLE `history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
--
-- AUTO_INCREMENT for table `state`
--
ALTER TABLE `state`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
