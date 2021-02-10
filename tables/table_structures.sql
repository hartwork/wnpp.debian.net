-- 
-- Debian WNPP related PHP/MySQL Scripts
-- 
-- Copyright (C) 2008 Sebastian Pipping <sebastian@pipping.org>
-- 
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
-- 
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
-- 
-- You should have received a copy of the GNU Affero General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.

-- phpMyAdmin SQL Dump
-- version 2.10.1
-- http://www.phpmyadmin.net

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

-- 
-- Table structure for table `debian_log_index`
-- 

DROP TABLE IF EXISTS `debian_log_index`;
CREATE TABLE `debian_log_index` (
  `log_id` int(11) NOT NULL auto_increment,
  `ident` int(11) default NULL,
  `type` enum('ITA','ITP','O','RFA','RFH','RFP') default 'RFH',
  `project` varchar(255) default NULL,
  `description` varchar(255) default NULL,
  `log_stamp` timestamp NULL default CURRENT_TIMESTAMP,
  `event` enum('OPEN','MOD','CLOSE') NOT NULL default 'MOD',
  `event_stamp` timestamp NULL default NULL,
  PRIMARY KEY  (`log_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=92 ;

-- --------------------------------------------------------

-- 
-- Table structure for table `debian_log_mods`
-- 

DROP TABLE IF EXISTS `debian_log_mods`;
CREATE TABLE `debian_log_mods` (
  `log_id` int(11) NOT NULL default '0',
  `before_type` enum('ITA','ITP','O','RFA','RFH','RFP') default NULL,
  `after_type` enum('ITA','ITP','O','RFA','RFH','RFP') default NULL,
  PRIMARY KEY  (`log_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

-- 
-- Table structure for table `debian_popcon`
-- 

DROP TABLE IF EXISTS `debian_popcon`;
CREATE TABLE `debian_popcon` (
  `package` varchar(255) NOT NULL default '',
  `inst` int(11) default NULL,
  `vote` int(11) default NULL,
  `old` int(11) default NULL,
  `recent` int(11) default NULL,
  `nofiles` int(11) default NULL,
  PRIMARY KEY  (`package`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

-- 
-- Table structure for table `debian_wnpp`
-- 

DROP TABLE IF EXISTS `debian_wnpp`;
CREATE TABLE `debian_wnpp` (
  `ident` int(11) NOT NULL default '0',
  `open_person` varchar(255) default NULL,
  `open_stamp` timestamp NULL default NULL,
  `mod_stamp` timestamp NULL default NULL,
  `type` enum('ITA','ITP','O','RFA','RFH','RFP') NOT NULL default 'RFH',
  `project` varchar(255) default NULL,
  `description` varchar(255) default NULL,
  `charge_person` varchar(255) default NULL,
  `cron_stamp` timestamp NOT NULL default CURRENT_TIMESTAMP,
  PRIMARY KEY  (`ident`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
