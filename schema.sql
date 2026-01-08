-- MySQL dump 10.13  Distrib 5.7.24, for osx10.9 (x86_64)
--
-- Host: localhost    Database: FLYTAU
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Aircraft`
--

DROP TABLE IF EXISTS `Aircraft`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Aircraft` (
  `aircraft_id` int NOT NULL,
  `manufacturer` varchar(50) NOT NULL,
  `size` varchar(20) NOT NULL,
  `purchase_date` date DEFAULT NULL,
  PRIMARY KEY (`aircraft_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Booking`
--

DROP TABLE IF EXISTS `Booking`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Booking` (
  `booking_id` varchar(10) NOT NULL,
  `email` varchar(255) NOT NULL,
  `flight_id` int NOT NULL,
  `booking_datetime` datetime DEFAULT CURRENT_TIMESTAMP,
  `total_price` decimal(10,2) NOT NULL,
  `booking_status` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`booking_id`),
  KEY `email` (`email`),
  KEY `flight_id` (`flight_id`),
  CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`email`) REFERENCES `Customer` (`email`),
  CONSTRAINT `booking_ibfk_2` FOREIGN KEY (`flight_id`) REFERENCES `Flight` (`flight_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Customer`
--

DROP TABLE IF EXISTS `Customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Customer` (
  `email` varchar(255) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Customer_Phone`
--

DROP TABLE IF EXISTS `Customer_Phone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Customer_Phone` (
  `email` varchar(255) NOT NULL,
  `phone_num` varchar(20) NOT NULL,
  PRIMARY KEY (`email`,`phone_num`),
  CONSTRAINT `customer_phone_ibfk_1` FOREIGN KEY (`email`) REFERENCES `Customer` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Flight`
--

DROP TABLE IF EXISTS `Flight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Flight` (
  `flight_id` int NOT NULL AUTO_INCREMENT,
  `route_id` int NOT NULL,
  `aircraft_id` int NOT NULL,
  `departure_date` date NOT NULL,
  `departure_time` time NOT NULL,
  `arrival_datetime` datetime DEFAULT NULL,
  `flight_status` varchar(20) DEFAULT 'Active',
  `price_economy` decimal(10,2) DEFAULT NULL,
  `price_business` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`flight_id`),
  KEY `route_id` (`route_id`),
  KEY `aircraft_id` (`aircraft_id`),
  CONSTRAINT `flight_ibfk_1` FOREIGN KEY (`route_id`) REFERENCES `Route` (`route_id`),
  CONSTRAINT `flight_ibfk_2` FOREIGN KEY (`aircraft_id`) REFERENCES `Aircraft` (`aircraft_id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Flight_Attendant`
--

DROP TABLE IF EXISTS `Flight_Attendant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Flight_Attendant` (
  `employee_id` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `employee_phone` varchar(20) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `street` varchar(50) DEFAULT NULL,
  `house_num` varchar(10) DEFAULT NULL,
  `is_qualified` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Flight_Attendant_on_Flights`
--

DROP TABLE IF EXISTS `Flight_Attendant_on_Flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Flight_Attendant_on_Flights` (
  `flight_id` int NOT NULL,
  `employee_id` varchar(20) NOT NULL,
  PRIMARY KEY (`flight_id`,`employee_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `flight_attendant_on_flights_ibfk_1` FOREIGN KEY (`flight_id`) REFERENCES `Flight` (`flight_id`),
  CONSTRAINT `flight_attendant_on_flights_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `Flight_Attendant` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Manager`
--

DROP TABLE IF EXISTS `Manager`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Manager` (
  `employee_id` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `employee_phone` varchar(20) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `street` varchar(50) DEFAULT NULL,
  `house_num` varchar(10) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  PRIMARY KEY (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Pilot`
--

DROP TABLE IF EXISTS `Pilot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Pilot` (
  `employee_id` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `employee_phone` varchar(20) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `street` varchar(50) DEFAULT NULL,
  `house_num` varchar(10) DEFAULT NULL,
  `is_qualified` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Pilots_on_Flights`
--

DROP TABLE IF EXISTS `Pilots_on_Flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Pilots_on_Flights` (
  `flight_id` int NOT NULL,
  `employee_id` varchar(20) NOT NULL,
  PRIMARY KEY (`flight_id`,`employee_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `pilots_on_flights_ibfk_1` FOREIGN KEY (`flight_id`) REFERENCES `Flight` (`flight_id`),
  CONSTRAINT `pilots_on_flights_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `Pilot` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Registered_Customer`
--

DROP TABLE IF EXISTS `Registered_Customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Registered_Customer` (
  `email` varchar(255) NOT NULL,
  `passport_num` varchar(20) DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `register_date` date DEFAULT NULL,
  PRIMARY KEY (`email`),
  CONSTRAINT `registered_customer_ibfk_1` FOREIGN KEY (`email`) REFERENCES `Customer` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Reserved_Seat`
--

DROP TABLE IF EXISTS `Reserved_Seat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Reserved_Seat` (
  `booking_id` varchar(10) NOT NULL,
  `aircraft_id` int NOT NULL,
  `row_num` int NOT NULL,
  `col_num` varchar(1) NOT NULL,
  PRIMARY KEY (`booking_id`,`aircraft_id`,`row_num`,`col_num`),
  KEY `aircraft_id` (`aircraft_id`,`row_num`,`col_num`),
  CONSTRAINT `reserved_seat_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `Booking` (`booking_id`),
  CONSTRAINT `reserved_seat_ibfk_2` FOREIGN KEY (`aircraft_id`, `row_num`, `col_num`) REFERENCES `Seat` (`aircraft_id`, `row_num`, `col_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Route`
--

DROP TABLE IF EXISTS `Route`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Route` (
  `route_id` int NOT NULL AUTO_INCREMENT,
  `origin` varchar(3) NOT NULL,
  `destination` varchar(3) NOT NULL,
  `duration` int NOT NULL,
  PRIMARY KEY (`route_id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Seat`
--

DROP TABLE IF EXISTS `Seat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Seat` (
  `aircraft_id` int NOT NULL,
  `row_num` int NOT NULL,
  `col_num` varchar(1) NOT NULL,
  `class` varchar(20) NOT NULL,
  PRIMARY KEY (`aircraft_id`,`row_num`,`col_num`),
  CONSTRAINT `seat_ibfk_1` FOREIGN KEY (`aircraft_id`) REFERENCES `Aircraft` (`aircraft_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-08 12:50:25
