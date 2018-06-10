<?php
/**
 * Debian WNPP related PHP/MySQL Scripts
 *
 * Copyright (C) 2008 Sebastian Pipping
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Sebastian Pipping, webmaster@hartwork.org
 */

include("config_inc.php5");
include("cron_shared.php5");


$LAST_RUN_FILENAME = "__last_sync_popcon_run";
$MINIMUM_RUN_GAP = 60 * 60 * 12; // 12 hours
$ENABLE_GAP_CHECK = TRUE;

$KEEP_FILES = 4;
$POPCON_DIR = sys_get_temp_dir() . "/popcon";


ob_implicit_flush(TRUE);
ob_end_flush();

function cleanup() {
    global $link;

    // Disconnect
    echo "LOCAL DISCONNECT\n";
    mysql_close($link);

    close_page();
}


function process($remote_url, $local_file_prefix) {
    global $POPCON_DIR;
    global $POPCON_TABLE;
    global $KEEP_FILES;

    $local_filename = "${POPCON_DIR}/${local_file_prefix}_" . date("Ymd_His"). ".gz";


    // Download
    echo "REMOTE READ\n";
    $online_file = @file_get_contents($remote_url);
    if (empty($online_file)) {
        echo "  ERROR\n";
        cleanup();
        exit(0);
    }
    echo "  SUCCESS\n";

    // Remove old files
    $old_files = glob("${POPCON_DIR}/${local_file_prefix}_????????_??????.gz");
    $count_old_files = count($old_files);
    $rem_files = max(0, $count_old_files - $KEEP_FILES);
    if ($rem_files > 0) {
        echo "LOCAL DELETE\n";
        for ($i = 1; $i <= $rem_files; $i++) {
            $file_to_delete = $old_files[$i];
            echo "  [$i/$rem_files] $file_to_delete\n";
            unlink($file_to_delete);
        }
    }

    // Write to file
    echo "LOCAL WRITE\n";
    $FILE = @fopen($local_filename, "w");
    if ($FILE) {
        $written_bytes = @fwrite($FILE, $online_file);
        @fclose($FILE);
        echo "  SUCCESS\n";
    } else {
        echo "  ERROR\n";
    }

    // Reading local file
    echo "LOCAL READ\n";
    $GZ_FILE = gzopen($local_filename, "rb");
    $matches = array();
    if ($GZ_FILE) {
        for (;;) {
            $line = gzgets($GZ_FILE);
            if (!$line) {
                if (!gzeof($GZ_FILE)) {
                    echo "  ERROR\n";
                }
                break;
            }

            if (!preg_match('/^\\d+\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)[^\r\n]*[\r\n]+$/', $line, $matches)) {
                continue;
            }

            $package = mysql_real_escape_string($matches[1]);
            $inst = mysql_real_escape_string($matches[2]);
            $vote = mysql_real_escape_string($matches[3]);
            $old = mysql_real_escape_string($matches[4]);
            $recent = mysql_real_escape_string($matches[5]);
            $nofiles = mysql_real_escape_string($matches[6]);

//            echo "  [$package][$inst][$vote][$old][$recent][$nofiles]\n";
            $query = "INSERT INTO $POPCON_TABLE (package,inst,vote,old,recent,nofiles) VALUES "
                    . "('$package',$inst,$vote,$old,$recent,$nofiles) ON DUPLICATE KEY UPDATE "
                    . "inst=$inst,vote=$vote,old=$old,recent=$recent,nofiles=$nofiles";
            $result = mysql_query($query);
        }
        gzclose($GZ_FILE);
    }
}


open_page();

if (!check_run_allowed()) {
    close_page();
    exit(0);
}

// Ensure directory presence
@mkdir($POPCON_DIR, 0750);

// Connect to database
echo "LOCAL CONNECT\n";
$link = mysql_connect($SERVER, $USERNAME, $PASSWORD);
if ($link === FALSE) {
    echo "  ERROR\n";
    exit(1);
}
echo "  SUCCESS\n";
mysql_select_db($DATABASE);

process('http://popcon.debian.org/source/by_inst.gz', 'source_by_inst_');
process('http://popcon.debian.org/by_inst.gz', 'binary_by_inst_');


cleanup();

?>
