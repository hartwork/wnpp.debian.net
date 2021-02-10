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

$LAST_RUN_FILENAME = sys_get_temp_dir() . "/__last_sync_list_run";
$MINIMUM_RUN_GAP = 55;
$ENABLE_GAP_CHECK = TRUE;

$ENABLE_REFRESH_HEADER = FALSE;
$REFRESH_INTERVAL = 60;
$MAX_SOAP_QUERIES = 201;
$TROUBLE_BLACKLIST = array(429035, 451077, 461925);


$done_soap_queries = 0;

ob_implicit_flush(TRUE);
ob_end_flush();

// Workaround SoapFault exceptions going to no-idea-where
function error_handler($code, $text) { }
set_error_handler('error_handler');

function cleanup() {
    global $link;

    // Disconnect
    echo "LOCAL DISCONNECT\n";
    mysql_close($link);

    close_page();
}

open_page();

/*
echo "BACK IN A FEW MINUTES\n";
exit(0);
*/

if (!check_run_allowed()) {
    close_page();
    exit(0);
}

// Connect to database
echo "LOCAL CONNECT\n";
$link = mysql_connect($SERVER, $USERNAME, $PASSWORD);
if ($link === FALSE) {
    echo "  ERROR\n";
    exit(1);
}
echo "  SUCCESS\n";
mysql_select_db($DATABASE);

// Get all related bug numbers
echo "REMOTE LIST\n";
$PACKAGE = 'wnpp';
try {
    $done_soap_queries++;
        $client = new SoapClient(NULL,
                array('location'     => "https://bugs.debian.org/cgi-bin/soap.cgi",
                'uri'     => "Debbugs/SOAP",
                'proxy_host'  => "https://bugs.debian.org"));

        $remote_idents = $client->__soapCall("get_bugs", array('package', $PACKAGE, 'status', 'open'));
} catch (Exception $e) {
    cleanup();
    exit(0);
}
echo "  " . count($remote_idents) . " entries in remote database, " . count($TROUBLE_BLACKLIST) . " blacklisted\n";

// Detect SQL injections
foreach ($remote_idents as $i) {
    if (!preg_match("/^\\d+$/", $i)) {
        echo "INSECURE '$i'\n";
        cleanup();
        exit(0);
    }
}

// Get all idents from database
echo "LOCAL LIST\n";
$result = mysql_query("SELECT ident FROM $WNPP_TABLE");
$count = mysql_num_rows($result);
$local_idents = array();
for ($i = 0; $i < $count; $i++) {
    $entry = mysql_fetch_row($result);
    $ident = $entry[0];
    array_push($local_idents, $ident);
}
echo "  " . count($local_idents) . " entries in local database\n";

// Diff
$local_only = array_diff($local_idents, $remote_idents);
$count_local_only = count($local_only);
$remote_only = array_diff(array_diff($remote_idents, $local_idents), $TROUBLE_BLACKLIST);
$count_remote_only = count($remote_only);

// Remove old bugs
if ($count_local_only > 0) {
    echo "LOCAL REMOVE\n";
    $delete_set = implode(",", $local_only);

    // Log entries
    $query = "INSERT INTO $LOG_INDEX_TABLE (ident,type,project,description,event,event_stamp) "
            . "SELECT ident,type,project,description,'CLOSE',NOW() "
            . "FROM $WNPP_TABLE WHERE ident IN ($delete_set)";
    $result = mysql_query($query);

    // Delete entries
    echo "  Removing $count_local_only entries\n";
    echo "  {" . $delete_set . "}\n";
    $query = "DELETE FROM $WNPP_TABLE WHERE ident IN ($delete_set)";
    $result = mysql_query($query);
}
$local_only = array();


function get_bug_soap($ident, $cur, $count, $isUpdate) {
    global $client;
    global $done_soap_queries;
    global $WNPP_TABLE;
    global $LOG_INDEX_TABLE;
    global $LOG_MODS_TABLE;

    echo "REMOTE QUERY [$cur/$count] " . ($isUpdate ? "UPDATE" : "ADD") . " $ident\n";
    try {
        $done_soap_queries++;
        $bugresponse = $client->__soapCall("get_status", array('bug'=>$ident));
    } catch (Exception $e) {
        echo "  EXCEPTION\n";
        return;
    }
    $bugobj = $bugresponse[$ident];

    if (!preg_match("/^(IT[AP]|O|RF[AHP]): ([^ ]+)(?: --?|:) (.+)$/", $bugobj->subject, $matches)) {
        echo "  FORMAT ERROR (pattern \"^(ITA|ITP|O|RFA|RFH|RFP): [^ ]+ -- .+\$\")\n";
        return;
    }

    $mod_stamp = mysql_real_escape_string($bugobj->log_modified);
    $type = $matches[1];
    $project = mysql_real_escape_string($matches[2]);
    $description = mysql_real_escape_string($matches[3]);
    $charge_person = mysql_real_escape_string($bugobj->owner);

    if ($isUpdate) {
        // Get current state
        $condition = "ident = '" . mysql_real_escape_string($ident) . "'";
        $query = "SELECT *,UNIX_TIMESTAMP(open_stamp) as unix_open_stamp FROM $WNPP_TABLE WHERE $condition";
        $result = mysql_query($query);
        $count = mysql_num_rows($result);
        if ($count != 1) {
            return;
        }
        $entry = mysql_fetch_assoc($result);

        // Compare
        $old_mod_stamp = $entry['unix_open_stamp'];
        $old_type = $entry['type'];
        $old_project = mysql_real_escape_string($entry['project']);
        $old_description = mysql_real_escape_string($entry['description']);
        $old_charge_person = mysql_real_escape_string($entry['charge_person']);

        $changes = array();
        if ($mod_stamp != $old_mod_stamp) {
            array_push($changes, "mod_stamp=FROM_UNIXTIME($mod_stamp)");
        }
        $type_changed = ($type != $old_type);
        if ($type_changed) {
            array_push($changes, "type='$type'");
            echo "  TYPE set from [$old_type] to [$type]\n";
        }
        if ($project != $old_project) {
            array_push($changes, "project='$project'");
            echo "  PROJECT set from [$old_project] to [$project]\n";
        }
        if ($description != $old_description) {
            array_push($changes, "description='$description'");
        }
        if ($charge_person != $old_charge_person) {
            array_push($changes, "charge_person='$charge_person'");
            echo "  OWNER set from [" . htmlspecialchars($old_charge_person)
                    . "] to [" . htmlspecialchars($charge_person) . "]\n";
        }

        // Update state
/*
        if (true) { // TODO Remove once filled, originator won't change
            $open_person = mysql_real_escape_string($bugobj->originator);
            array_push($changes, "open_person='$open_person'");
        }
*/
        array_push($changes, "cron_stamp=NOW()");
        $updates = implode(", ", $changes);
        $query = "UPDATE $WNPP_TABLE SET $updates WHERE $condition";
        $result = mysql_query($query);

        if ($type_changed) {
            // Log entry
            $query = "INSERT INTO $LOG_INDEX_TABLE (ident,type,project,description,event,event_stamp) "
                    . "SELECT ident,type,project,description,'MOD',FROM_UNIXTIME($mod_stamp) FROM $WNPP_TABLE WHERE "
                    . "ident = '$ident'";
            $result = mysql_query($query);

            // Log details
            $query = "INSERT INTO $LOG_MODS_TABLE (log_id,before_type,after_type) "
                    . "VALUES "
                    . "(LAST_INSERT_ID(),'$old_type','$type')";
            $result = mysql_query($query);
        }
    } else {
        // Add
        $open_person = mysql_real_escape_string($bugobj->originator);
        $open_stamp = mysql_real_escape_string($bugobj->date);
        echo "  [$ident][$type][$project][$description]\n";

        // Bug data
        $query = "INSERT INTO $WNPP_TABLE (ident,open_person,open_stamp,mod_stamp,type,project,description,charge_person) "
                . "VALUES "
                . "($ident,'$open_person',FROM_UNIXTIME(${open_stamp}),FROM_UNIXTIME(${mod_stamp}),'$type',"
                . "'$project','$description','$charge_person')";
        $result = mysql_query($query);

        // Log entry
        $query = "INSERT INTO $LOG_INDEX_TABLE (ident,type,project,description,event,event_stamp) "
                . "SELECT ident,type,project,description,'OPEN',open_stamp FROM $WNPP_TABLE WHERE "
                . "ident = '$ident'";
        $result = mysql_query($query);

        echo "  ADDED\n";
    }
}

// Add new bugs
if ($count_remote_only > 0) {
    echo "LOCAL ADD\n";
    echo "  Adding $count_remote_only entries\n";
    $entries_to_grab = min($MAX_SOAP_QUERIES - $done_soap_queries, $count_remote_only);
    for ($i = 0; $i < $entries_to_grab; $i++) {
        $ident = array_pop($remote_only);
        get_bug_soap($ident, $i + 1, $entries_to_grab, FALSE);
    }
}

// Update existing bugs
echo "LOCAL UPDATE\n";
$entries_to_update = $MAX_SOAP_QUERIES - $done_soap_queries;
$query = "SELECT ident FROM $WNPP_TABLE ORDER BY cron_stamp ASC LIMIT $entries_to_update";
$result = mysql_query($query);
$entries_to_update = mysql_num_rows($result);

if ($entries_to_update > 0) {
    echo "  Checking " . $entries_to_update . " entries for updates\n";

    for ($i = 0; $i < $entries_to_update; $i++) {
        $entry = mysql_fetch_row($result);
        $ident = $entry[0];
        get_bug_soap($ident, $i + 1, $entries_to_update, TRUE);
    }
}

cleanup();
exit(0);

?>
