-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 25, 2020 at 09:03 PM
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
(1, '2020-08-26 02:03:34', 1, 47.7, 47.7, 7.701, 7.701),
(2, '2020-08-26 02:03:34', 2, 45.5, 46.1, 7.701, 7.701),
(3, '2020-08-26 02:03:34', 3, 49.1, 49.1, 7.693, 7.693),
(4, '2020-08-26 02:03:34', 4, 45.9, 46.7, 7.69, 7.69),
(5, '2020-08-26 02:03:34', 5, 47, 47, 7.689, 7.688),
(6, '2020-08-26 02:03:34', 6, 45, 45, 7.686, 7.686),
(7, '2020-08-26 02:03:34', 7, 46.1, 46.1, 7.69, 7.69),
(8, '2020-08-26 02:03:34', 9, 43.8, 43.8, 7.686, 7.686),
(9, '2020-08-26 02:03:34', 10, 46.4, 46.4, 7.68, 7.68),
(10, '2020-08-26 02:03:34', 11, 45.7, 45.7, 7.673, 7.673),
(11, '2020-08-26 02:03:34', 12, 46, 46, 7.656, 7.656),
(12, '2020-08-26 02:03:34', 13, 47.4, 47.4, 7.648, 7.648),
(13, '2020-08-26 02:03:34', 14, 46.5, 46.5, 7.646, 7.646),
(14, '2020-08-26 02:03:34', 15, 48, 47.9, 7.638, 7.638),
(15, '2020-08-26 02:03:34', 16, 46.8, 46.8, 7.643, 7.643);

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
(1, '2020-08-25 23:13:49', 'charger', 'once', 0),
(3, '2020-08-26 02:03:34', 'ac_present', '1', 60),
(4, '2020-08-26 02:03:34', 'ignition', '0', 60),
(5, '2020-08-26 02:03:34', 'charging', '1', 60),
(6, '2020-08-26 02:03:34', 'front_t_av', '47', 60),
(7, '2020-08-26 02:03:34', 'back_t_av', '46', 60),
(8, '2020-08-26 02:03:34', 'v', '115.1', 60),
(9, '2020-08-26 02:03:34', 'v_av', '7.67', 60),
(10, '2020-08-26 02:03:34', 'v_min', '7.64', 60),
(11, '2020-08-26 02:03:34', 'v_max', '7.70', 60),
(12, '2020-08-26 02:03:35', 'front_polling_period', '1.73', 0),
(13, '2020-08-26 02:03:34', 'back_polling_period', '1.75', 0),
(14, '2020-08-25 23:09:07', 'trip_odometer', '0.0', 0),
(15, '2020-08-25 23:14:56', 'charge_odometer', '0.0', 0),
(16, '2020-08-15 22:30:35', 'heat_on_c', '23.0', 0),
(17, '2020-08-15 22:30:44', 'heat_off_c', '24.0', 0),
(18, '2020-08-26 02:03:34', 'speed', '0', 0),
(19, '2020-08-16 00:22:47', 'controller_temp', '0', 300),
(20, '2020-08-16 00:26:14', 'charge_wh', '0.0', 0),
(21, '2020-08-16 00:40:47', 'amps', '0.0', 0),
(22, '2020-08-16 16:29:19', 'wifi', 'at_home', 0),
(23, '2020-08-26 02:03:34', 'lat', '45.017259', 0),
(24, '2020-08-26 02:03:34', 'lon', '-93.355322000', 0),
(25, '2020-08-26 02:03:34', 'ip', '42.108', 0),
(26, '2020-08-26 02:03:32', 'v_acc_batt', '12.30', 60),
(27, '2020-08-26 02:03:34', 'v_i_sense', '2.176', 60),
(28, '2020-08-26 02:02:15', 'dcdc', 'disabled', 0);
(29, '2020-08-26 02:02:15', 'controller_fan', 'disabled', 0);

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7922;
--
-- AUTO_INCREMENT for table `state`
--
ALTER TABLE `state`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
