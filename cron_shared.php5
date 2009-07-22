<?php

function open_page() {
    global $ENABLE_REFRESH_HEADER;
    global $REFRESH_INTERVAL;

    echo "<html>";
    if ($ENABLE_REFRESH_HEADER) {
        echo "<head>";
        echo "<meta http-equiv=\"Refresh\" content=\"" . $REFRESH_INTERVAL . "; url=\">";
        echo "</head>";
    }
    echo "<body>";
    echo "<pre>\n";
}

function close_page() {
    echo "\nDONE.\n";

    echo "</pre>";
    echo "</body>";
    echo "</html>\n";
}

function check_run_allowed() {
    global $ENABLE_GAP_CHECK;
    global $LAST_RUN_FILENAME;
    global $MINIMUM_RUN_GAP;

    if (!$ENABLE_GAP_CHECK) {
        return TRUE;
    }

    echo "CHECK TIME OF LAST RUN\n";
    $atime = @fileatime($LAST_RUN_FILENAME);
    if ($atime) {
        $seconds_since_last_run = (time() - $atime);
        if ($seconds_since_last_run < $MINIMUM_RUN_GAP) {
            echo "  GAP TOO SMALL (come back in " . ($MINIMUM_RUN_GAP - $seconds_since_last_run) . " seconds)\n";
            return FALSE;
        }
    }

    touch($LAST_RUN_FILENAME);
    return TRUE;
}

?>
