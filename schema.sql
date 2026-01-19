-- MySQL dump 10.13  Distrib 5.7.24, for osx10.9 (x86_64)
--
-- Host: localhost    Database: flytau
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

INSERT INTO Aircraft (aircraft_id, manufacturer, size, purchase_date) VALUES
(1, 'Daso', 'Small', '2026-01-13'),
(2, 'Airbus', 'Big', '2026-01-12'),
(3, 'Boeing', 'Small', '2026-01-07'),
(4, 'Daso', 'Big', '2026-01-12'),
(5, 'Airbus', 'Big', '2026-01-06'),
(6, 'Airbus', 'Small', '2026-01-07'),
(7, 'Airbus', 'Small', '2025-12-30'),
(8, 'Boeing', 'Small', '2026-01-01');

INSERT INTO Route (route_id, origin, destination, duration) VALUES
(1,  'TLV', 'FRA', 265),
(2,  'FRA', 'TLV', 265),
(3,  'TLV', 'MUC', 255),
(4,  'MUC', 'TLV', 255),
(5,  'TLV', 'BCN', 270),
(6,  'BCN', 'TLV', 270),
(7,  'TLV', 'VIE', 200),
(8,  'VIE', 'TLV', 200),
(9,  'TLV', 'ZRH', 250),
(10, 'ZRH', 'TLV', 250),
(11, 'TLV', 'WAW', 215),
(12, 'WAW', 'TLV', 215),
(13, 'TLV', 'PRG', 240),
(14, 'PRG', 'TLV', 240),
(15, 'TLV', 'DEL', 420),
(16, 'DEL', 'TLV', 420),
(17, 'TLV', 'SIN', 675),
(18, 'SIN', 'TLV', 675),
(19, 'TLV', 'EWR', 660),
(20, 'EWR', 'TLV', 660);



INSERT INTO Customer (email, first_name, last_name) VALUES
('gall@gmail.com', 'gal',   'oosh'),
('im@mail.com',    'im',    'ro'),
('imri@gmail.com', 'imri',  'rong'),
('king@gmail.com', 'king',  'james'),
('tamar@gmail.com','tamat', 'tami'),
('yosi@gmail.com', 'yosi',  'yosi');



INSERT INTO Pilot
(employee_id, first_name, last_name, employee_phone, start_date, city, street, house_num, is_qualified)
VALUES
('211266572', 'גן', 'דיברומאן', '0524547744', '2026-01-14', 'תל אביב', 'גאולה', '1', 1),
('223434456', 'נועה', 'קליין', '0552211345', '2025-09-21', 'סביון', 'פארק', '99', 1),
('232212125', 'רות', 'קליינשמיט', '0565654545', '2026-01-02', 'כפר הדרים', 'שקד', '30', 0),
('232356788', 'חן', 'אצקין', '0523355789', '2025-08-21', 'רעננה', 'שיא', '43', 0),
('323322567', 'נעם', 'ריבין', '0553456788', '2019-02-13', 'תל אביב', 'בציר', '67', 1),
('323445668', 'איתי', 'לוי', '0555555855', '2025-03-02', 'קריית אונו', 'אור', '23', 0),
('324252627', 'יובל', 'כהן', '0523453451', '2025-01-05', 'רמת גן', 'הרצל', '77', 0),
('324266787', 'דור', 'פרץ', '0528878965', '2025-11-04', 'תל אביב', 'הכרמל', '30', 1),
('343432323', 'חן', 'קליינשמיט', '0523434545', '2023-12-08', 'כפר שמריהו', 'נחל', '2', 1),
('344344566', 'דניאל', 'פרץ', '0538866456', '2025-09-27', 'סביון', 'רימון', '99', 0),
('435564323', 'יושי', 'לובק', '0587744234', '2025-06-10', 'רמת גן', 'ניצן', '78', 1),
('554434567', 'עדי', 'עמדי', '0556778654', '2025-07-17', 'כפר סבא', 'באילן', '106', 1),
('565643434', 'יואב', 'פז', '0547788543', '2024-11-29', 'רחובות', 'אלמוג', '52', 0),
('768776523', 'יונתן', 'מזרחי', '0565533678', '2026-01-13', 'הרצליה', 'החצב', '67', 0),
('878865786', 'עליזה', 'מכלוף', '0543355789', '2023-06-15', 'כפר סבא', 'השלוש', '31', 1);



INSERT INTO Flight_Attendant
(employee_id, first_name, last_name, employee_phone, start_date, city, street, house_num, is_qualified)
VALUES
('0523736765', 'בר', 'זק', '0636057865', '2025-12-29', 'בר', 'בר', '2', 1),
('0524049988', 'דן', 'גלז', '056667765', '2025-12-29', 'מכבי', 'מכבי', '1', 1),
('0525087766', 'איימי', 'הכלה', '0864743354', '2025-12-30', 'תל אביב', 'ירדן', '12', 1),
('0667191866', 'מפצח', 'החל', '0547676866', '2025-12-31', 'מכבי', 'שבע', '7', 1),
('0757938738', 'אורי', 'חזקה', '052948498', '2025-12-29', 'דן', 'נחל', '1', 1),
('21212121', 'דן', 'מנו', '0523766565', '2025-12-28', 'דן', 'דן', '1', 0),
('212332445', 'ליעם', 'חכמון', '0545567545', '2025-08-11', 'הרצליה', 'הרצל', '98', 0),
('22222232', 'אבי', 'נימני', '0588888888', '2025-12-28', 'תל אביב', 'מכבי', '8', 1),
('22232333', 'קנדי', 'הכלה', '097965656', '2025-12-29', 'שהם', 'שגיא', '45', 0),
('22326546', 'יוסי', 'בנין', '0533322333', '2025-12-30', 'בית שאן', 'ליברפול', '1', 1),
('224243443', 'בר', 'זומר', '0535565575', '2025-12-31', 'כפר סבא', 'ורד', '1', 1),
('2242628876', 'אילת', 'אילת', '0525058654', '2026-01-07', 'שהם', 'הגבעה', '1', 1),
('2245478789', 'אמרי', 'רונג', '0534477656', '2026-01-05', 'כפר הס', 'הקטיף', '1', 1),
('225242676', 'בן', 'זיני', '052304987', '2026-01-13', 'תל אביב', 'ורד', '9', 1),
('225276866', 'סול', 'סול', '053446544', '2026-01-01', 'גבעתיים', 'ים', '4', 1),
('225533678', 'נעם', 'קליינשטיין', '0548855112', '2025-07-17', 'תל אביב', 'הרדוף', '30', 1),
('225769876', 'משה', 'קצת', '0525058889', '2025-12-31', 'כללי', 'קצאות', '1', 1),
('226776865', 'שחר', 'חסן', '0532868686', '2026-01-01', 'תל אביב', 'כלנית', '2', 1),
('232322123', 'עפר', 'מיינר', '0536644567', '2025-12-14', 'חיפה', 'דן', '88', 0),
('23235435', 'גל', 'הרמן', '224232121', '2026-01-08', 'שהם', 'הדר', '1', 1),
('232445656', 'בר', 'רפאלי', '0554667822', '2025-11-03', 'רעות', 'מכבים', '67', 1),
('233244567', 'סלים', 'טואמה', '0555555566', '2025-10-18', 'ליגה', 'לאומית', '0', 0),
('233434345', 'קרן', 'פלס', '0546600443', '2025-07-28', 'בורגתה', 'סחלב', '76', 1),
('234235456', 'מירי', 'מסיקה', '0541122112', '2025-08-31', 'תל מונד', 'נובמבר', '11', 1),
('325575766', 'עדי', 'הימלבלוי', '0527864565', '2026-01-07', 'הרצליה', 'שמנונה', '2', 1);


INSERT INTO Manager
(employee_id, first_name, last_name, employee_phone, start_date, city, street, house_num, password)
VALUES
('0525059897', 'לברון', 'ג׳ימס', '05687785546', '2026-01-14', 'תל אביב', 'אלון', '23', 'kcrui'),
('1', 'אור', 'סופר', '0501234567', '2024-01-01', 'Tel Aviv', 'Herzl', '10', '123'),
('12345678', 'ערן', 'צק', '0521234567', '2026-01-01', 'תל אביב', 'הירקון', '100', '12345678');


INSERT INTO Seat (aircraft_id, row_num, col_num, class) VALUES
(1, 1, 'A', 'Economy'),
(1, 1, 'B', 'Economy'),
(1, 2, 'A', 'Economy'),
(1, 2, 'B', 'Economy'),

(2, 1, 'A', 'Business'),
(2, 1, 'B', 'Business'),
(2, 2, 'A', 'Business'),
(2, 2, 'B', 'Business'),
(2, 3, 'A', 'Economy'),
(2, 3, 'B', 'Economy'),
(2, 4, 'A', 'Economy'),
(2, 4, 'B', 'Economy'),

(3, 1, 'A', 'Economy'),
(3, 1, 'B', 'Economy'),
(3, 1, 'C', 'Economy'),
(3, 2, 'A', 'Economy'),
(3, 2, 'B', 'Economy'),
(3, 2, 'C', 'Economy'),

(4, 1, 'A', 'Business'),
(4, 2, 'A', 'Business'),
(4, 3, 'A', 'Economy'),
(4, 4, 'A', 'Economy'),

(5, 1, 'A', 'Business'),
(5, 1, 'B', 'Business'),
(5, 2, 'A', 'Business'),
(5, 2, 'B', 'Business'),
(5, 3, 'A', 'Economy'),
(5, 3, 'B', 'Economy'),
(5, 4, 'A', 'Economy'),
(5, 4, 'B', 'Economy'),

(6, 1, 'A', 'Economy'),
(6, 1, 'B', 'Economy'),
(6, 1, 'C', 'Economy'),
(6, 2, 'A', 'Economy'),
(6, 2, 'B', 'Economy'),
(6, 2, 'C', 'Economy'),
(6, 3, 'A', 'Economy'),
(6, 3, 'B', 'Economy'),
(6, 3, 'C', 'Economy'),

(7, 1, 'A', 'Economy'),
(7, 1, 'B', 'Economy'),
(7, 1, 'C', 'Economy'),
(7, 2, 'A', 'Economy'),
(7, 2, 'B', 'Economy'),
(7, 2, 'C', 'Economy'),

(8, 1, 'A', 'Economy'),
(8, 1, 'B', 'Economy'),
(8, 2, 'A', 'Economy'),
(8, 2, 'B', 'Economy'),
(8, 3, 'A', 'Economy'),
(8, 3, 'B', 'Economy');



INSERT INTO Flight (
    flight_id,
    route_id,
    aircraft_id,
    departure_date,
    departure_time,
    arrival_datetime,
    flight_status,
    price_economy,
    price_business
) VALUES
(1,  5,  1, '2026-01-14', '15:26:00', '2026-01-14 19:56:00', 'Active',     350.00, 0.00),
(2,  6,  1, '2026-01-16', '15:28:00', '2026-01-16 19:58:00', 'Active',     450.00, 0.00),
(3, 15,  2, '2026-02-20', '16:27:00', '2026-02-20 23:27:00', 'Active',     690.00, 4300.00),
(4,  9,  6, '2026-02-28', '17:30:00', '2026-02-28 21:40:00', 'Active',     400.00, 0.00),
(5, 10,  6, '2026-03-01', '20:36:00', '2026-03-02 00:46:00', 'Active',     600.00, 0.00),
(6, 13,  3, '2026-03-03', '19:36:00', '2026-03-03 23:36:00', 'Full',       560.00, 0.00),
(7,  3,  7, '2025-12-18', '15:45:00', '2025-12-18 20:00:00', 'Performed',  120.00, 0.00),
(8,  4,  7, '2025-12-31', '15:47:00', '2025-12-31 20:02:00', 'Performed',  300.00, 0.00);





INSERT INTO Registered_Customer (
    email,
    passport_num,
    birth_date,
    password,
    register_date
) VALUES
('imri@gmail.com', '35551087', '2022-03-10', '678',   '2026-01-13'),
('yosi@gmail.com', '45678',    '2025-12-30', '12345', '2026-01-13');

INSERT INTO Customer_Phone (email, phone_num) VALUES
('gall@gmail.com',  '05434868565'),
('im@mail.com',     '0569489484'),
('imri@gmail.com',  '0525256666'),
('king@gmail.com',  '050232323'),
('tamar@gmail.com', '06868687474'),
('yosi@gmail.com',  '05433232477');

INSERT INTO Booking (
    booking_id,
    email,
    flight_id,
    booking_datetime,
    total_price,
    booking_status
) VALUES
('3G02U2TZ', 'yosi@gmail.com', 5, '2026-01-13 15:39:09',  90.00,   'Cancelled by Customer'),
('DTX3E83J', 'yosi@gmail.com', 5, '2026-01-13 15:40:20', 2400.00, 'Active'),
('F90366TH', 'imri@gmail.com', 1, '2026-01-13 15:38:00', 700.00,  'Active'),
('GUXZMK0J', 'yosi@gmail.com', 3, '2026-01-13 15:39:30', 4990.00, 'Active'),
('H7D4DDIJ', 'imri@gmail.com', 6, '2026-01-13 15:37:40', 1680.00, 'Active'),
('MKLL2ZY4', 'king@gmail.com', 6, '2026-01-13 15:35:09', 1680.00, 'Active'),
('RPB2P73M', 'gall@gmail.com', 4, '2026-01-13 15:40:59', 800.00,  'Active'),
('VZWWNFEJ', 'im@mail.com',    8, '2025-12-17 15:45:40', 600.00,  'Performed'),
('WYM30ELB', 'tamar@gmail.com',7, '2025-12-17 15:44:59', 600.00,  'Performed');



INSERT INTO Pilots_on_Flights (flight_id, employee_id) VALUES
(7, '211266572'),
(8, '211266572'),

(7, '223434456'),
(8, '223434456'),

(4, '232356788'),
(5, '232356788'),
(6, '232356788'),

(3, '343432323'),

(1, '435564323'),
(2, '435564323'),
(3, '435564323'),

(4, '565643434'),
(5, '565643434'),
(6, '565643434'),

(1, '878865786'),
(2, '878865786'),
(3, '878865786');

INSERT INTO Flight_Attendant_on_Flights (flight_id, employee_id) VALUES
(1, '0523736765'),
(2, '0523736765'),
(3, '0523736765'),

(7, '0524049988'),
(8, '0524049988'),

(3, '0525087766'),
(3, '066719186'),

(7, '0757938738'),
(8, '0757938738'),

(1, '21212121'),
(2, '21212121'),

(6, '212332445'),

(7, '22222232'),
(8, '22222232'),

(4, '22223233'),
(5, '22223233'),
(6, '22223233'),

(3, '2242628876'),
(3, '225276866'),
(6, '225533678'),
(3, '225769876'),

(4, '226776865'),
(5, '226776865'),

(1, '23235435'),
(2, '23235435'),
(4, '23235435'),
(5, '23235435');

INSERT INTO Reserved_Seat (booking_id, aircraft_id, row_num, col_num) VALUES
('F90366TH', 1, 1, 'A'),
('F90366TH', 1, 1, 'B'),

('GUXZMK0J', 2, 1, 'B'),
('GUXZMK0J', 2, 4, 'A'),

('MKLL2ZY4', 3, 1, 'A'),
('MKLL2ZY4', 3, 1, 'B'),
('MKLL2ZY4', 3, 1, 'C'),

('H7D4DDIJ', 3, 2, 'A'),
('H7D4DDIJ', 3, 2, 'B'),
('H7D4DDIJ', 3, 2, 'C'),

('RPB2P73M', 6, 1, 'A'),
('RPB2P73M', 6, 1, 'B'),

('DTX3E83J', 6, 1, 'B'),
('DTX3E83J', 6, 1, 'C'),
('DTX3E83J', 6, 2, 'A'),
('DTX3E83J', 6, 2, 'B'),

('WYM30ELB', 7, 1, 'A'),
('WYM30ELB', 7, 1, 'B'),
('WYM30ELB', 7, 1, 'C'),
('WYM30ELB', 7, 2, 'A'),
('WYM30ELB', 7, 2, 'B'),

('VZWWNFEJ', 7, 1, 'C'),
('VZWWNFEJ', 7, 2, 'A');






