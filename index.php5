<?php
/**
 * Debian WNPP related PHP/MySQL Scripts
 *
 * Copyright (C) 2008-2009 Sebastian Pipping <sebastian@pipping.org>
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

// MySQL >=4.1.x required

include("config_inc.php5");

$TITLE = "Debian Packages that Need Lovin'";
$MAX_PROJECT_LEN = 20;
$MAX_DESCR_LEN = 60;


// Get order settings
function other_direction_lower($dir) {
    return ($dir == "ASC") ? "desc" : "asc";
}

function to_order_col($user_col) {
    switch ($user_col) {
    case "dust": return "mod_stamp";
    case "age": return "open_stamp";
    case "users": return "vote";
    case "installs": return "inst";
    case "owner": return "charge_person";
    case "reporter": return "open_person";
    default: return $user_col;
    }
}

function get_sort_part_for_column($user_col) {
    global $order_col;
    global $order_dir;

    switch ($user_col) {
    case "age": // FALLTRHOUGH
    case "dust":
        return "sort=$user_col;" . (($order_col == to_order_col($user_col))
                ? strtolower($order_dir)
                : "asc");
    default:
        return "sort=$user_col;" . (($order_col == to_order_col($user_col))
                ? other_direction_lower($order_dir)
                : "asc");
    }
}

if (empty($_GET['sort'])) {
    $_GET['sort'] = "project";
}
$matches = array();
if (!preg_match("/^(dust|age|type|project|users|installs|owner|reporter)(?:;((?:a|de)sc))?$/", $_GET['sort'], $matches)) {
    $order_col = 'project';
    $order_dir = 'ASC';
} else {
    $order_col = to_order_col($matches[1]);
    $order_dir = ($matches[2] == "") ? "ASC" : strtoupper($matches[2]);

    // Age must be inverted, proper column name
    switch ($order_col) {
    case "open_stamp": // FALLTROUGH
    case "mod_stamp": // FALLTROUGH
        $order_dir = ($order_dir == "ASC") ? "DESC" : "ASC";
        break;
    } 
}
$sort_part = "sort=$order_col;" . strtolower($order_dir);



// Get owner settings
$with_owner = FALSE;
$without_owner = FALSE;

if (isset($_GET['owner'])) {
    foreach($_GET['owner'] as $owner) {
        switch ($owner) {
        case "yes": $with_owner = TRUE; break;
        case "no": $without_owner = TRUE; break;
        }
    }
}

$owners = array();
if ($with_owner) { array_push($owners, "yes"); }
if ($without_owner) { array_push($owners, "no"); }

if (empty($owners)) {
    $owner_match = '1';
    $owner_uri_part = '';

    $with_owner = TRUE;
    $without_owner = TRUE;
} else {
    if ($with_owner && $without_owner) {
        $owner_match = '1';
        $owner_uri_part = '';
    } else {
        $OWNER_KEY = to_order_col('owner');
        if ($with_owner) {
            $owner_match = "(($OWNER_KEY IS NOT NULL) AND ($OWNER_KEY != ''))";
            $owner_uri_part = 'owner%5B%5D=yes&';
        } else {
            $owner_match = "(($OWNER_KEY IS NULL) OR ($OWNER_KEY = ''))";
            $owner_uri_part = 'owner%5B%5D=no&';
        }
    }
}



// Get type settings
$show_ita = FALSE;
$show_itp = FALSE;
$show_o = FALSE;
$show_rfa = FALSE;
$show_rfh = FALSE;
$show_rfp = FALSE;

if (isset($_GET['type'])) {
    foreach($_GET['type'] as $type) {
        switch ($type) {
        case "ITA": $show_ita = TRUE; break;
        case "ITP": $show_itp = TRUE; break;
        case "O":   $show_o   = TRUE; break;
        case "RFA": $show_rfa = TRUE; break;
        case "RFH": $show_rfh = TRUE; break;
        case "RFP": $show_rfp = TRUE; break;
        }
    }
}

$types = array();
if ($show_ita) { array_push($types, "ITA"); }
if ($show_itp) { array_push($types, "ITP"); }
if ($show_o  ) { array_push($types, "O"  ); }
if ($show_rfa) { array_push($types, "RFA"); }
if ($show_rfh) { array_push($types, "RFH"); }
if ($show_rfp) { array_push($types, "RFP"); }

$DEFAULT_SHOW_ITA = FALSE;
$DEFAULT_SHOW_ITP = FALSE;
$DEFAULT_SHOW_O = TRUE;
$DEFAULT_SHOW_RFA = TRUE;
$DEFAULT_SHOW_RFH = TRUE;
$DEFAULT_SHOW_RFP = TRUE;

if (empty($types)) {
    $type_match = 'type NOT IN (\'ita\',\'itp\')';
    $type_uri_part = '';

    $show_ita = $DEFAULT_SHOW_ITA;
    $show_itp = $DEFAULT_SHOW_ITP;
    $show_o = $DEFAULT_SHOW_O;
    $show_rfa = $DEFAULT_SHOW_RFA;
    $show_rfh = $DEFAULT_SHOW_RFH;
    $show_rfp = $DEFAULT_SHOW_RFP;
} else {
    if (($show_ita == $DEFAULT_SHOW_ITA)
            && ($show_itp == $DEFAULT_SHOW_ITP)
            && ($show_o == $DEFAULT_SHOW_O)
            && ($show_rfa == $DEFAULT_SHOW_RFA)
            && ($show_rfh == $DEFAULT_SHOW_RFH)
            && ($show_rfp == $DEFAULT_SHOW_RFP)) {
        $type_uri_part = '';
    } else {
        $type_uri_part = "type%5B%5D=" . implode("&type%5B%5D=", $types) . "&";
    }

    if (count($types) == 6) { // XXX
        $type_match = '1';
    } else {
        $type_match = "type IN ('" . implode("','", $types) . "')";
    }
}



// Get col settings
$show_dust = FALSE;
$show_age = FALSE;
$show_type = FALSE;
$show_description = FALSE;
$show_users = FALSE;
$show_installs = FALSE;
$show_owner = FALSE;
$show_reporter = FALSE;

if (isset($_GET['col'])) {
    foreach($_GET['col'] as $col) {
        switch ($col) {
        case "dust": $show_dust = TRUE; break;
        case "age": $show_age = TRUE; break;
        case "type": $show_type = TRUE; break;
        case "description": $show_description = TRUE; break;
        case "users": $show_users = TRUE; break;
        case "installs": $show_installs = TRUE; break;
        case "owner": $show_owner = TRUE; break;
        case "reporter": $show_reporter = TRUE; break;
        }
    }
}

$cols = array();
if ($show_dust) { array_push($cols, "dust"); }
if ($show_age) { array_push($cols, "age"); }
if ($show_type) { array_push($cols, "type"); }
if ($show_description) { array_push($cols, "description"); }
if ($show_users) { array_push($cols, "users"); }
if ($show_installs) { array_push($cols, "installs"); }
if ($show_owner) { array_push($cols, "owner"); }
if ($show_reporter) { array_push($cols, "reporter"); }


$DEFAULT_SHOW_DUST = TRUE;
$DEFAULT_SHOW_AGE = FALSE;
$DEFAULT_SHOW_TYPE = TRUE;
$DEFAULT_SHOW_DESCRIPTION = TRUE;
$DEFAULT_SHOW_USERS = FALSE;
$DEFAULT_SHOW_INSTALLS = TRUE;
$DEFAULT_SHOW_OWNER = FALSE;
$DEFAULT_SHOW_REPORTER = FALSE;

if (empty($cols)) {
    $col_uri_part = '';

    $show_dust = $DEFAULT_SHOW_DUST;
    $show_age = $DEFAULT_SHOW_AGE;
    $show_type = $DEFAULT_SHOW_TYPE;
    $show_description = $DEFAULT_SHOW_DESCRIPTION;
    $show_users = $DEFAULT_SHOW_USERS;
    $show_installs = $DEFAULT_SHOW_INSTALLS;
    $show_owner = $DEFAULT_SHOW_OWNER;
    $show_reporter = $DEFAULT_SHOW_REPORTER;
} else {
    if (($show_dust == $DEFAULT_SHOW_DUST)
            && ($show_age == $DEFAULT_SHOW_AGE)
            && ($show_type == $DEFAULT_SHOW_TYPE)
            && ($show_description == $DEFAULT_SHOW_DESCRIPTION)
            && ($show_users == $DEFAULT_SHOW_USERS)
            && ($show_installs == $DEFAULT_SHOW_INSTALLS)
            && ($show_owner == $DEFAULT_SHOW_OWNER)
            && ($show_reporter == $DEFAULT_SHOW_REPORTER)) {
        $col_uri_part = '';
    } else {
        $col_uri_part = "col%5B%5D=" . implode("&col%5B%5D=", $cols) . "&";
    }
}



// Magic quotes
// http://de3.php.net/manual/en/security.magicquotes.php#59438
if (get_magic_quotes_gpc()) {
    echo "Magic quotes is borking the request data. php.ini missing?";
    exit(1);
}

// Page header
echo "<html>\n";
echo "<head>\n";
echo "<meta http-equiv=\"Content-Type\" content=\"text/html;charset=utf-8\">\n";
echo "<title>$TITLE</title>\n";

// Colors selected with help from the Color schemes generator 2
// http://wellstyled.com/tools/colorscheme2/index-en.html

// derived from     blue     orange      green        red
$COLORS = array('#FFCCFF', '#FFFFCC', '#CCFFFF', '#FFCCCC');

echo "<style>\n";
echo "    * { font-family: 'Bitstream Vera Sans', 'Verdana', Sans-Serif; }\n";
echo "    table.data_table { border:1px solid #C0C0C0; background-color:#C0C0C0; }\n";
echo "    table.form_table { border:2px solid #C0C0C0; background-color:#F8F8F8; }\n";
echo "    th { background-color:#F8F8F8; }\n";
echo "    td, input, select, body { font-size: 10.5pt; }\n";
echo "    td.ITA { background-color: #FFFFFF; }\n";
echo "    td.ITP { background-color: #FFFFFF; }\n";
echo "    td.O { background-color: $COLORS[3]; }\n";
echo "    td.RFA { background-color: $COLORS[1]; }\n";
echo "    td.RFH { background-color: $COLORS[0]; }\n";
echo "    td.RFP { background-color: $COLORS[2]; }\n";
echo "</style>\n";

echo "</head>\n";
echo "<body style=\"margin:0;\">\n";

echo "<table width=\"100%\" bgcolor=\"#C0C0C0\" cellspacing=\"0\" cellpadding=\"0\">\n";
echo "<tr>\n";
echo "    <td align=\"left\">\n";
echo "        <table cellspacing=\"0\" cellpadding=\"0\">\n";
echo "        <tr>\n";
echo "            <td valign=\"center\" style=\"padding:1 2 1 4;\"><img src=\"images/feed-icon.png\" width=\"20\" height=\"20\"></td>\n";
echo "            <td valign=\"center\" style=\"margin:0;padding:0;\">\n";
echo "                <form action=\"news.php5\" method=\"GET\" style=\"margin:0;padding:2;\">\n";
echo "                <select name=\"data\" size=\"1\" style=\"background-color:#C0C0C0;\">\n";
echo "                    <option value=\"all\">All Changes</option>\n";
echo "                    <option value=\"good_news\">Good News</option>\n";
echo "                    <option value=\"bad_news\">Bad News</option>\n";
echo "                    <option value=\"help_existing\" selected>Help Existing Packages</option>\n";
echo "                    <option value=\"new_packages\">New Packages</option>\n";
echo "                </select> <select name=\"title_format\" size=\"1\" style=\"background-color:#C0C0C0;\">\n";
echo "                    <option value=\"0\" selected>Default Title Format (0)</option>\n";
echo "                    <option value=\"1\">Alternative Title Format (1)</option>\n";
echo "                </select> <input type=\"submit\" value=\"Feed\">\n";
echo "                </form>\n";
echo "            </td>\n";
echo "        </tr>\n";
echo "        </table>\n";
echo "    </td>\n";
echo "    <td align=\"right\">\n";
echo "        <table cellspacing=\"0\" cellpadding=\"0\">\n";
echo "        <tr>\n";
echo "            <td valign=\"center\" style=\"padding:1 2 1 2;\"><img src=\"images/valid-rss-20.png\" width=\"57\" height=\"20\"></td>\n";
echo "            <td valign=\"center\" style=\"margin:0;padding:0;\">\n";
echo "                <form action=\"http://feedvalidator.org/check.cgi\" method=\"GET\" style=\"margin:0;padding:2;\">\n";
echo "                <input type=\"hidden\" name=\"url\" value=\"http://wnpp.debian.net/news.php5?data=all&amp;amp;title_format=0\">\n";
echo "                <input type=\"submit\" value=\"Validate\">\n";
echo "                </form>\n";
echo "            </td>\n";
echo "        </tr>\n";
echo "        </table>\n";
echo "    </td>\n";
echo "</tr>\n";
echo "<tr>\n";
echo "    <td bgcolor=\"#000000\" colspan=\"2\" style=\"font-size:1px\">&nbsp;</td>\n";
echo "</tr>\n";
echo "</table>\n";
echo "<br>\n";






echo "<table width=\"100%\">\n";
echo "<tr>\n";
echo "    <td align=\"center\">\n";
echo "        <h1>$TITLE</h1>\n";
echo "        <form action=\"\" method=\"get\">\n";
echo "        <table cellspacing=\"1\" class=\"form_table\">\n";
echo "        <tr>\n";
echo "            <td>\n";
echo "                <table>\n";
echo "                <tr>\n";
echo "                    <td valign=\"top\">\n";
echo "                        <select multiple size=\"8\" name=\"type[]\">\n";
echo "                        <option " . ($show_ita ? "selected " : "") . "value=\"ITA\">ITA&nbsp;</option>\n";
echo "                        <option " . ($show_itp ? "selected " : "") . "value=\"ITP\">ITP&nbsp;</option>\n";
echo "                        <option " . ($show_o   ? "selected " : "") . "value=\"O\">O&nbsp;</option>\n";
echo "                        <option " . ($show_rfa ? "selected " : "") . "value=\"RFA\">RFA&nbsp;</option>\n";
echo "                        <option " . ($show_rfh ? "selected " : "") . "value=\"RFH\">RFH&nbsp;</option>\n";
echo "                        <option " . ($show_rfp ? "selected " : "") . "value=\"RFP\">RFP&nbsp;</option>\n";
echo "                        </select>\n";
echo "                    </td>\n";
echo "                    <td valign=\"top\">\n";
echo "                        <table height=\"100%\">\n";
echo "                        <tr>\n";
echo "                            <td>\n";
echo "                                <table>\n";
echo "                                <tr>\n";
echo "                                    <td>Project:</td>\n";
if (!empty($_GET['project'])) {
    $project_filter = htmlspecialchars($_GET['project']);
    $project_uri_part = "project=" . urlencode($_GET['project']) . "&";
} else {
    $project_filter = "";
    $project_uri_part = "";
}
echo "                                    <td><input type=\"text\" size=\"24\" name=\"project\" value=\"$project_filter\"></td>\n";
echo "                                </tr>\n";
echo "                                <tr>\n";
echo "                                    <td>Description:</td>\n";
if (!empty($_GET['description'])) {
    $description_filter = htmlspecialchars($_GET['description']);
    $description_uri_part = "description=" . urlencode($_GET['description']) . "&";
} else {
    $description_filter = "";
    $description_uri_part = "";
}
echo "                                    <td><input type=\"text\" size=\"24\" name=\"description\" value=\"$description_filter\"></td>\n";
echo "                                </tr>\n";
echo "                                <tr>\n";
echo "                                    <td>Owner:</td>\n";
echo "                                    <td><input type=\"checkbox\" name=\"owner[]\" value=\"yes\"" . ($with_owner ? "checked " : "") . ">With"
        . "&nbsp;&nbsp;<input type=\"checkbox\" name=\"owner[]\" value=\"no\"" . ($without_owner ? "checked " : "") . ">Without</td>\n";
echo "                                </tr>\n";
echo "                                </table>\n";
echo "                            </td>\n";
echo "                        </tr>\n";
echo "                        <tr>\n";
echo "                            <td valign=\"bottom\">\n";
echo "                                <table width=\"100%\">\n";
echo "                                <tr>\n";
echo "                                    <td align=\"left\"><a href=\"cron_sync_list.php5\" target=\"_blank\">Sync bugs</a> <a href=\"cron_sync_popcon.php5\" target=\"_blank\">Sync popcon</a></td>\n";
echo "                                    <td align=\"right\"><input type=\"submit\" value=\"Query\"></td>\n";
echo "                                </tr>\n";
echo "                                </table>\n";
echo "                            </td>\n";
echo "                        </tr>\n";
echo "                        </table>\n";
echo "                    </td>\n";
echo "                    <td valign=\"top\">\n";
echo "                        <select multiple size=\"8\" name=\"col[]\">\n";
echo "                        <option " . ($show_dust ? "selected " : "") . "value=\"dust\">Dust</option>\n";
echo "                        <option " . ($show_age ? "selected " : "") . "value=\"age\">Age</option>\n";
echo "                        <option " . ($show_type ? "selected " : "") . "value=\"type\">Type</option>\n";
echo "                        <option " . ($show_description ? "selected " : "") . "value=\"description\">Description</option>\n";
echo "                        <option " . ($show_users ? "selected " : "") . "value=\"users\">Users</option>\n";
echo "                        <option " . ($show_installs ? "selected " : "") . "value=\"installs\">Installs</option>\n";
echo "                        <option " . ($show_owner ? "selected " : "") . "value=\"owner\">Owner</option>\n";
echo "                        <option " . ($show_reporter ? "selected " : "") . "value=\"reporter\">Reporter</option>\n";
echo "                        </select>\n";
echo "                    </td>\n";
echo "                </tr>\n";
echo "                </table>\n";
echo "            </td>\n";
echo "        </tr>\n";
echo "        </table>\n";
if (!empty($_GET['sort'])) {
echo "        <input type=\"hidden\" name=\"sort\" value=\"" . htmlspecialchars($_GET['sort']) . "\">\n";
}
echo "        </form>\n";


// Connect
$link = mysql_connect($SERVER, $USERNAME, $PASSWORD);
mysql_select_db($DATABASE);

function make_like_chain($user_col, $words, $empty_value, $op) {
    if (empty($words)) {
        return $empty_value;
    }

    return "($user_col LIKE '%" . implode("%') $op ($user_col LIKE '%", $words) . "%')";
}

function make_condition($get_var, $user_col) {
    if (!isset($_GET[$get_var])) {
        return "1";
    }

    if ($user_col == "") {
        $user_col = $get_var;
    }

    $words = explode(" ", mysql_real_escape_string($_GET[$get_var]));
    if (empty($words)) {
        return "1";
    }

    $positive = array();
    $negative = array();
    $matches = array();

    foreach($words as $i) {
        if (!preg_match("/^([+-]?)(.+)$/", $i, $matches)) {
            continue;
        }

        $signum = $matches[1];
        // Fix for SQL
        $word = str_replace(array('_', '%'), array('\_','\%'), $matches[2]);
        if ($signum == "-") {
            array_push($negative, $word);
        } else {
            array_push($positive, $word);
        }
    }

    $cond_positive = make_like_chain($user_col, $positive, "1", "AND");
    $cond_negative = make_like_chain($user_col, $negative, "0", "OR");

    return "(($cond_positive) AND NOT ($cond_negative))";
}

$project_match = make_condition("project", "project");
$description_match = make_condition("description", "description");



// Get list
$condition = "($type_match AND $project_match AND $description_match AND $owner_match)";

// What columns do we need
$query_cols = array();
array_push($query_cols, 'GROUP_CONCAT(ident ORDER BY ident ASC SEPARATOR \',\') AS ident_list');
if ($show_dust) { array_push($query_cols, 'UNIX_TIMESTAMP(' . to_order_col('dust') . ') AS unix_mod_stamp'); }
if ($show_age) { array_push($query_cols, 'UNIX_TIMESTAMP(' . to_order_col('age') . ') AS unix_open_stamp'); }
array_push($query_cols, 'type');
array_push($query_cols, 'project');
if ($show_description) { array_push($query_cols, to_order_col('description')); }
if ($show_users) { array_push($query_cols, to_order_col('users')); }
if ($show_installs) { array_push($query_cols, to_order_col('installs')); }
if ($show_owner) { array_push($query_cols, to_order_col('owner')); }
if ($show_reporter) { array_push($query_cols, to_order_col('reporter')); }

$col_part = implode(',', $query_cols);
$query = "SELECT $col_part "
        . "FROM $WNPP_TABLE " . (($show_users || $show_installs) ? "LEFT JOIN $POPCON_TABLE ON project = package " : ' ')
        . "WHERE $condition GROUP BY project ORDER BY ${order_col} ${order_dir}";
$result = mysql_query($query);
// echo "[$query]<br>\n"; // XXX
$count = $result ? mysql_num_rows($result) : 0;



// Legend
echo "ITA/ITP = <i>Intent to <u>p</u>ackage/<u>a</u>dopt</i> ..... O = <i><u>O</u>rphaned</i> ..... RFA/RFH/RFP = <i>Request for <u>a</u>doption/<u>h</u>elp/<u>p</u>ackaging</i><br>\n";
echo "<br>\n";

echo "    </td>\n";
echo "</tr>\n";
echo "</table>\n";
echo "<table width=\"100%\">\n";
echo "<tr>\n";
echo "    <td align=\"center\">\n";

// Table header
// NOTE: Order should match that appearing in the form to give identical URLs where possible
$uri_part_but_sort = "?" . $type_uri_part . $project_uri_part . $description_uri_part . $owner_uri_part . $col_uri_part;
echo "<table cellpadding=\"4\" cellspacing=\"1\" class=\"data_table\">\n";
echo "<tr>";
    echo "<th align=\"right\">&nbsp;#&nbsp;</th>";
    if ($show_dust) {
        echo "<th>&nbsp;<a href=\"" . $uri_part_but_sort . get_sort_part_for_column('dust') . "\" title=\"Number of days without changes\">Dust</a>&nbsp;</th>";
    }
    if ($show_age) {
        echo "<th>&nbsp;<a href=\"" . $uri_part_but_sort . get_sort_part_for_column('age') . "\" title=\"Number of days since this bug's creation\">Age</a>&nbsp;</th>";
    }
    if ($show_type) {
        echo "<th><a href=\"" . $uri_part_but_sort . get_sort_part_for_column('type') . "\">Type</a></th>";
    }
    echo "<th><a href=\"" . $uri_part_but_sort . get_sort_part_for_column('project') . "\">Project</a></th>";
    if ($show_description) {
        echo "<th>Description</th>";
    }
    if ($show_users) {
        echo "<th>&nbsp;<a href=\"" . $uri_part_but_sort . get_sort_part_for_column('users') . "\" title=\"Minimum number of people using this package on a regular basis\">Users</a>&nbsp;</th>";
    }
    if ($show_installs) {
        echo "<th>&nbsp;<a href=\"" . $uri_part_but_sort . get_sort_part_for_column('installs') . "\" title=\"Minimum number of people having this package installed\">Installs</a>&nbsp;</th>";
    }
    if ($show_owner) {
        echo "<th><a href=\"" . $uri_part_but_sort . get_sort_part_for_column('owner') . "\">Owner</a></th>";
    }
    if ($show_reporter) {
        echo "<th><a href=\"" . $uri_part_but_sort . get_sort_part_for_column('reporter') . "\">Reporter</a></th>";
    }
echo "</tr>\n";

/*
// http://de3.php.net/manual/en/function.utf8-decode.php#51417
function is_utf8($string) {
    return (preg_match('/^(?:[\x00-\x7f]|[\xc0-\xdf][\x80-\xbf]|[\xe0-\xef][\x80-\xbf]{2}'
            . '|[\xf0-\xf7][\x80-\xbf]{3}|[\xf8-\xfb][\x80-\xbf]{4}|'
            . '[\xfc-\xfd][\x80-\xbf]{5})*$/', $string) === 1);
}
*/

// http://de3.php.net/manual/en/function.ucwords.php#76786
function custom_cap($name) {
    // $name = strtolower($name);
    $name = mb_strtolower($name, "UTF-8");
    $name = join("'", array_map('ucwords', explode("'", $name)));
    $name = join("-", array_map('ucwords', explode("-", $name)));
    $name = join("Mac", array_map('ucwords', explode("Mac", $name)));
    $name = join("Mc", array_map('ucwords', explode("Mc", $name)));
    return $name;
}

/* TEST CASES
    Tyler Macdonald
    Marc-andr Lureau
    Mario Izquierdo \(mariodebian\)
    Aurlien Grme
    Chanop Silpa-anan
*/

function name_only($mail_and_name) {
    if (empty($mail_and_name)) {
        return "<i>nobody</i>";
    }

    $matches = array();
    if (!preg_match("/^([^@]+)\s+<[^>]+>$/", $mail_and_name, $matches)) {
        return "<i>hidden</i>";
    }

        $text = str_replace("\"", "", $matches[1]);
        $text = str_replace(array("\\(", "\\)"), array("(", ")"), $text);
    return htmlspecialchars(custom_cap($text));
}

function shrink($text, $maxlen) {
    return (strlen($text) > $maxlen)
            ? substr($text, 0, $maxlen - 4) . "[..]"
            : $text;
}

function null_is_zero($value) {
    return empty($value) ? 0 : $value;
}

// Table body, get single entries
for ($i = 0; $i < $count; $i++) {
    $entry = mysql_fetch_assoc($result);

    echo "<tr>";
        $row = $i + 1;
        $type = $entry['type'];
        echo "<td class=\"$type\" align=\"right\">&nbsp;$row&nbsp;</td>";

        if ($show_dust) {
            $dust = (int)((time() - $entry['unix_mod_stamp']) / 60 / 60 / 24);
            echo "<td class=\"$type\" align=\"right\">&nbsp;$dust&nbsp;</td>";
        }
        if ($show_age) {
            $age = (int)((time() - $entry['unix_open_stamp']) / 60 / 60 / 24);
            echo "<td class=\"$type\" align=\"right\">&nbsp;$age&nbsp;</td>";
        }
        if ($show_type) {
            echo "<td class=\"$type\"><nobr>$type</nobr></td>";
        }

        $project = shrink($entry['project'], $MAX_PROJECT_LEN);
        $ident_list = explode(',', $entry['ident_list']);
        $count_ident_list = count($ident_list);
        $url_base = 'http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=';
        $project_cell = '';
        if ($count_ident_list == 0) {
            $project_cell = '<nobr><i>ERROR</i></nobr>';
        } else if ($count_ident_list == 1) {
            $project_cell = '<nobr><a href="' . $url_base . $ident_list[0] . '">' . $project . '</a></nobr>';
        } else {
            $project_cell = "<nobr>$project ";
            for ($j = 0; $j < $count_ident_list; $j++) {
                $project_cell .= ('<a href="' . $url_base . $ident_list[$j] . '">[' . ($j + 1) . ']</a>');
            }
            $project_cell .= '</nobr>';
        }
        echo "<td class=\"$type\">$project_cell</td>";

        if ($show_description) {
            $description = shrink($entry['description'], $MAX_DESCR_LEN);
            echo "<td class=\"$type\"><nobr>$description</nobr></td>";
        }
        if ($show_users) {
            $users = null_is_zero($entry['vote']);
            echo "<td class=\"$type\" align=\"right\"><nobr>&nbsp;$users&nbsp;</nobr></td>";
        }
        if ($show_installs) {
            $installs = null_is_zero($entry['inst']);
            echo "<td class=\"$type\" align=\"right\"><nobr>&nbsp;$installs&nbsp;</nobr></td>";
        }
        if ($show_owner) {
            $owner = name_only($entry['charge_person']);
            echo "<td class=\"$type\"><nobr>$owner</nobr></td>";
        }
        if ($show_reporter) {
            $reporter = name_only($entry['open_person']);
            echo "<td class=\"$type\"><nobr>$reporter</nobr></td>";
        }
    echo "</tr>\n";
}

// Page footer
echo "</table><br>\n";
echo "    </td>\n";
echo "</tr>\n";
echo "<tr>\n";
echo "    <td align=\"center\" style=\"padding-bottom:10px\">\n";

echo "Written by <a href=\"mailto:sebastian@pipping.org\">Sebastian Pipping</a>.&nbsp;&nbsp;<a href=\"http://git.goodpoint.de/?p=wnpp-debian-net.git\">Sources</a> licensed under <a href=\"http://www.fsf.org/licensing/licenses/agpl.html\">AGPL 3.0 or later.</a>\n";

echo "    </td>\n";
echo "</tr>\n";
echo "</table>\n";

echo "</body>\n";
echo "</html>\n";

// Disconnect
mysql_close($link);

?>
