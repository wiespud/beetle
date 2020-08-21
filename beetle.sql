-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 20, 2020 at 07:36 PM
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
(1, '2020-08-21 00:36:28', 1, 36, 37.2, 8.036, 8.036),
(2, '2020-08-21 00:36:28', 2, 35.3, 35.8, 8.038, 8.038),
(3, '2020-08-21 00:36:28', 3, 37.2, 37.2, 8.033, 8.033),
(4, '2020-08-21 00:36:28', 4, 35.9, 35.9, 8.031, 8.031),
(5, '2020-08-21 00:36:28', 5, 39.4, 39.4, 8.03, 8.03),
(6, '2020-08-21 00:36:28', 6, 36.7, 36.8, 8.026, 8.026),
(7, '2020-08-21 00:36:28', 7, 36.9, 36.8, 8.025, 8.026),
(8, '2020-08-21 00:36:27', 9, 34.9, 34.9, 8.025, 8.025),
(9, '2020-08-21 00:36:27', 10, 37.5, 37.9, 8.021, 8.021),
(10, '2020-08-21 00:36:27', 11, 36.9, 37, 8.014, 8.014),
(11, '2020-08-21 00:36:27', 12, 39.3, 39.3, 7.998, 7.998),
(12, '2020-08-21 00:36:27', 13, 39.8, 39.8, 7.991, 7.991),
(13, '2020-08-21 00:36:27', 14, 37.9, 37.9, 7.986, 7.986),
(14, '2020-08-21 00:36:27', 15, 39, 39, 7.975, 7.975),
(15, '2020-08-21 00:36:27', 16, 38.1, 37.2, 7.978, 7.978);

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
(1, '2020-08-20 14:39:38', 'charger', 'disabled', 0),
(3, '2020-08-21 00:36:28', 'ac_present', '1', 60),
(4, '2020-08-21 00:36:27', 'ignition', '0', 60),
(5, '2020-08-21 00:36:28', 'charging', '0', 60),
(6, '2020-08-21 00:36:29', 'front_t_av', '37', 60),
(7, '2020-08-21 00:36:27', 'back_t_av', '38', 60),
(8, '2020-08-21 00:36:27', 'v', '120.2', 60),
(9, '2020-08-21 00:36:27', 'v_av', '8.01', 60),
(10, '2020-08-21 00:36:27', 'v_min', '7.97', 60),
(11, '2020-08-21 00:36:27', 'v_max', '8.04', 60),
(12, '2020-08-21 00:36:28', 'front_polling_period', '1.78', 0),
(13, '2020-08-21 00:36:28', 'back_polling_period', '1.70', 0),
(14, '2020-08-19 22:26:40', 'trip_odometer', '29.8', 0),
(15, '2020-08-20 01:03:16', 'charge_odometer', '0.0', 0),
(16, '2020-08-15 22:30:35', 'heat_on_c', '23.0', 0),
(17, '2020-08-15 22:30:44', 'heat_off_c', '24.0', 0),
(18, '2020-08-21 00:36:28', 'speed', '0', 0),
(19, '2020-08-16 00:22:47', 'controller_temp', '0.0', 60),
(20, '2020-08-16 00:26:14', 'charge_wh', '0.0', 0),
(21, '2020-08-16 00:40:47', 'amps', '0.0', 0),
(22, '2020-08-16 16:29:19', 'wifi', 'at_home', 0),
(23, '2020-08-21 00:36:28', 'lat', '45.017251', 0),
(24, '2020-08-21 00:36:28', 'lon', '-93.355241667', 0),
(25, '2020-08-21 00:36:28', 'ip', '.42.108', 0);

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4101;
--
-- AUTO_INCREMENT for table `state`
--
ALTER TABLE `state`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
