<?php
/**
 * Debian WNPP related PHP/MySQL Scripts
 *
 * Copyright (C) 2008 Sebastian Pipping <sebastian@pipping.org>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

include("config_inc.php5");
include("cron_shared.php5");

$DEBUG = FALSE;

function open_feed() {
    global $DEBUG;
    if ($DEBUG) {
        header("Content-type: text/plain");
    } else {
        header("Content-type: application/rss+xml");
    }

    echo "<?xml version=\"1.0\"?>\n";
    echo "<rss version=\"2.0\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n";
    echo "  <channel>\n";
    echo "\n";
}

// Title style
if (!empty($_GET['title_format'])) {
    $title_format = $_GET['title_format'];
} else {
    $title_format = 0;
}
switch ($title_format) {
case 0:
case 1:
    break;

default:
    $title_format = 0;
}

// Data set
if (!empty($_GET['data'])) {
    $data = $_GET['data'];
} else {
    $data = 'all';
}

switch ($data) {
case 'new_packages':
    $CONDITION = "(event = 'CLOSE') AND (type = 'ITP')";
    $FEED_TITLE = "New Debian Packages";
    break;

case 'good_news':
    $CONDITION = "(event = 'CLOSE') OR ((event IN ('MOD','OPEN')) AND (type IN ('ITA','ITP')))";
    $FEED_TITLE = "Good News on Debian Packages";
    break;

case 'bad_news':
    $CONDITION = "!((event = 'CLOSE') OR ((event IN ('MOD','OPEN')) AND (type IN ('ITA','ITP'))))";
    $FEED_TITLE = "Bad News on Debian Packages";
    break;

case 'help_existing':
    $CONDITION = "(event IN ('OPEN','MOD')) AND (type IN ('O','RFA','RFH'))";
    $FEED_TITLE = "Existing Debian Packages In Need For Help";
    break;

case 'all': // fall through
default:
    $data = 'all';
    $CONDITION = "1";
    $FEED_TITLE = "Debian Packaging News";
    break;
}

$DATA_QUERY = "SELECT ident,type,before_type,after_type,project,description,event,UNIX_TIMESTAMP(event_stamp) AS unix_event_stamp "
        . "FROM $LOG_INDEX_TABLE LEFT JOIN $LOG_MODS_TABLE ON $LOG_INDEX_TABLE.log_id = $LOG_MODS_TABLE.log_id "
        . "WHERE $CONDITION ORDER BY event_stamp DESC LIMIT 30";
$MAX_QUERY = "SELECT UNIX_TIMESTAMP(MAX(event_stamp)) AS unix_event_stamp FROM $LOG_INDEX_TABLE WHERE $CONDITION";

function print_feed_header($unix_content_change) {
    global $data;
    global $title_format;
    global $DEBUG;
    global $FEED_TITLE;
    $lastBuildDate = date('r', $unix_content_change);
    $self_url = "http://wnpp.debian.net/news.php5?data=$data&amp;amp;title_format=$title_format";

    if (!$DEBUG) {
        echo "    <title>$FEED_TITLE</title>\n";
    }
    echo "    <link>$self_url</link>\n";
    echo "    <atom:link href=\"$self_url\" rel=\"self\" type=\"application/rss+xml\" />\n";
    echo "    <description>Debian news feed on packaging bugs</description>\n";
    echo "    <language>en-us</language>\n";
    echo "    <pubDate>$lastBuildDate</pubDate>\n";
    echo "    <lastBuildDate>$lastBuildDate</lastBuildDate>\n";
    echo "    <webMaster>webmaster@hartwork.org (Sebastian Pipping)</webMaster>\n";
    echo "    <ttl>15</ttl>\n"; // because the cron runs every 30 minutes
    echo "\n";
}

function close_feed() {
    echo "\n";
    echo "  </channel>\n";
    echo "</rss>\n";
}

function cleanup() {
    global $link;

    // Disconnect
    mysql_close($link);

    close_feed();
}

open_feed();

// Connect to database
$link = mysql_connect($SERVER, $USERNAME, $PASSWORD);
mysql_select_db($DATABASE);

function escape_xml($text) {
    // Extensible Markup Language (XML) 1.0 (Fourth Edition)
    // 2.4 Character Data and Markup
    // http://www.w3.org/TR/REC-xml/#syntax
    return str_replace(array('&', '<', '>', '\'', '"'),
            array('&amp;', '&lt;', '&gt;', '&apos;', '&quot;'),
            $text);
}

function print_entry($entry) {
    global $title_format;

    $type = $entry['type'];
    $after_type = $entry['after_type'];
    $before_type = $entry['before_type'];
    $ident = $entry['ident'];
    $project = $entry['project'];
    $description = $entry['description'];
    $event = $entry['event'];
    $rfc822 = date("r", $entry['unix_event_stamp']);
    $guid_layout = ($entry['unix_event_stamp'] <= 1202047202 + 1200) ? 0 : 1;

    switch($event) {
    case 'CLOSE':
        $type_title_part = $type;
        $event_title_part = "Closed";
        break;

    case 'MOD': // fall through
        $type_title_part = "$before_type -> $after_type";
        $event_title_part = "Modified";
        break;

    case 'OPEN': // fall through
    default:
        $type_title_part = $type;
        $event_title_part = "Opened";
        break;
    }

    switch ($title_format) {
    case 1:
        if ($event != 'CLOSE') {
            $title = '#' . "$ident $type_title_part: $project -- $description";
        } else {
            $title = "CLOSED : $project -- $description";
        }
        break;

    case 0: // fall through
    default:
        $title = "$event_title_part [$type_title_part] $project -- $description";
    }
    $title = escape_xml($title);

    $url = 'http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=' . $ident;
    switch ($guid_layout) {
    case 1:
        $guid = 'http://wnpp.debian.net/' . $ident . '/' . $entry['unix_event_stamp'];
        break;

    case 0: // fall through
    default:
        $guid = 'http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=' . $ident;
        break;

    }
    $author = $ident . '@bugs.debian.org';

    echo "    <item>\n";
    echo "      <title>$title</title>\n";
    echo "      <link>$url</link>\n";
    echo "      <description>$url</description>\n";
    echo "      <pubDate>$rfc822</pubDate>\n";
    echo "      <guid>$guid</guid>\n";
    echo "      <dc:creator>$author</dc:creator>\n";
    echo "    </item>\n";
}

// Feed header
$query = $MAX_QUERY;
$result = mysql_query($query);
if (!$result) {
    cleanup();
    exit(0);
}
$entry = mysql_fetch_assoc($result);
$unix_content_change = $entry['unix_event_stamp'];
print_feed_header($unix_content_change);

// Feed data
$query = $DATA_QUERY;
// echo "[$query]\n";
$result = mysql_query($query);
if (!$result) {
    cleanup();
    exit(0);
}
$count = mysql_num_rows($result);
for ($i = 0; $i < $count; $i++) {
    $entry = mysql_fetch_assoc($result);
    print_entry($entry);
}

cleanup();

?>
