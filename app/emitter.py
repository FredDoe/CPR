# -*- coding: utf-8 -*-

import sys
import os
from app import definitions, values, logger
import textwrap
from app.synthesis import program_to_code

rows, columns = os.popen("stty size", "r").read().split()

GREY = "\t\x1b[1;30m"
RED = "\t\x1b[1;31m"
GREEN = "\x1b[1;32m"
YELLOW = "\t\x1b[1;33m"
BLUE = "\t\x1b[1;34m"
ROSE = "\t\x1b[1;35m"
CYAN = "\x1b[1;36m"
WHITE = "\t\x1b[1;37m"

PROG_OUTPUT_COLOR = "\t\x1b[0;30;47m"
STAT_COLOR = "\t\x1b[0;32;47m"


def write(print_message, print_color, new_line=True, prefix=None, indent_level=0):
    if not values.silence_emitter:
        message = "\033[K" + print_color + str(print_message) + "\x1b[0m"
        if prefix:
            prefix = "\033[K" + print_color + str(prefix) + "\x1b[0m"
            len_prefix = ((indent_level + 1) * 4) + len(prefix)
            wrapper = textwrap.TextWrapper(
                initial_indent=prefix,
                subsequent_indent=" " * len_prefix,
                width=int(columns),
            )
            message = wrapper.fill(message)
        sys.stdout.write(message)
        if new_line:
            r = "\n"
            sys.stdout.write("\n")
        else:
            r = "\033[K\r"
            sys.stdout.write(r)
        sys.stdout.flush()


def title(title):
    write("\n" + "=" * 100 + "\n\n\t" + title + "\n" + "=" * 100 + "\n", CYAN)
    logger.information(title)


def sub_title(subtitle):
    write("\n\t" + subtitle + "\n\t" + "_" * 90 + "\n", CYAN)
    logger.information(subtitle)


def sub_sub_title(sub_title):
    write("\n\t\t" + sub_title + "\n\t\t" + "-" * 90 + "\n", CYAN)
    logger.information(sub_title)


def command(message):
    if values.DEBUG:
        prefix = "\t\t[command] "
        write(message, ROSE, prefix=prefix, indent_level=2)
    logger.command(message)


def debug(message):
    if values.DEBUG:
        prefix = "\t\t[debug] "
        write(message, GREY, prefix=prefix, indent_level=2)
    logger.debug(message)


def data(message, info=None):
    if values.DEBUG:
        prefix = "\t\t[data] "
        write(message, GREY, prefix=prefix, indent_level=2)
        if info:
            write(info, GREY, prefix=prefix, indent_level=2)
    logger.data(message, info)


def normal(message, jump_line=True):
    write(message, BLUE, jump_line)
    logger.output(message)


def highlight(message, jump_line=True):
    indent_length = message.count("\t")
    prefix = "\t" * indent_length
    message = message.replace("\t", "")
    write(message, WHITE, jump_line, indent_level=indent_length, prefix=prefix)
    logger.note(message)


def emit_patch(patch_tree, jump_line=True, message=""):
    output = message
    for lid, prog in patch_tree.items():
        code = lid + ": " + (program_to_code(prog))
    for comp_var, prog_var in values.MAP_PROG_VAR.items():
        code = code.replace(comp_var, prog_var)
    indent_length = 0
    prefix = "\t" * indent_length
    output = output + code
    write(output, WHITE, jump_line, indent_level=indent_length, prefix=prefix)
    logger.data(message, code, True)


def information(message, jump_line=True):
    if values.DEBUG:
        write(message, GREY, jump_line)
    logger.information(message)


def statistics(message):
    write(message, WHITE)
    logger.output(message)


def error(message):
    write(message, RED)
    logger.error(message)


def success(message):
    write(message, GREEN)
    logger.output(message)


def special(message):
    write(message, ROSE)
    logger.note(message)


def program_output(output_message):
    write("\t\tProgram Output:", WHITE)
    if type(output_message) == list:
        for line in output_message:
            write("\t\t\t" + line.strip(), PROG_OUTPUT_COLOR)
    else:
        write("\t\t\t" + output_message, PROG_OUTPUT_COLOR)


def emit_var_map(var_map):
    write("\t\tVar Map:", WHITE)
    for var_a in var_map:
        highlight("\t\t\t " + var_a + " ==> " + var_map[var_a])


def emit_ast_script(ast_script):
    write("\t\tAST Script:", WHITE)
    for line in ast_script:
        special("\t\t\t " + line.strip())


def warning(message):
    write(message, YELLOW)
    logger.warning(message)


def note(message):
    write(message, WHITE)
    logger.note(message)


def configuration(setting, value):
    message = "\t[config] " + setting + ": " + str(value)
    write(message, WHITE, True)
    logger.configuration(setting + ":" + str(value))


def end(time_info, is_error=False):
    if values.CONF_ARG_PASS:
        statistics("\nRun time statistics:\n-----------------------\n")
        statistics(
            "Startup: "
            + str(time_info[definitions.KEY_DURATION_BOOTSTRAP].format())
            + " minutes"
        )
        statistics(
            "Build: " + str(time_info[definitions.KEY_DURATION_BUILD]) + " minutes"
        )
        statistics(
            "Testing: "
            + str(time_info[definitions.KEY_DURATION_INITIALIZATION])
            + " minutes"
        )
        statistics("Synthesis: " + str(values.TIME_TO_GENERATE) + " minutes")
        statistics("Explore: " + format(values.TIME_TO_EXPLORE, ".3f") + " minutes")
        statistics("Refine: " + format(values.TIME_TO_REDUCE, ".3f") + " minutes")
        statistics(
            "Reduce: " + str(time_info[definitions.KEY_DURATION_REPAIR]) + " minutes"
        )
        statistics("Iteration Count: " + str(values.ITERATION_NO))
        # statistics("Patch Gen Count: " + str(values.COUNT_PATCH_GEN))
        statistics("Patch Explored Count: " + str(values.COUNT_PATCHES_EXPLORED))
        statistics("Patch Start Count: " + str(values.COUNT_PATCH_START))
        statistics("Patch End Seed Count: " + str(values.COUNT_PATCH_END_SEED))
        statistics("Patch End Count: " + str(values.COUNT_PATCH_END))
        if values.DEFAULT_PATCH_TYPE == values.OPTIONS_PATCH_TYPE[1]:
            statistics(
                "Template Explored Count: " + str(values.COUNT_TEMPLATES_EXPLORED)
            )
            # statistics("Template Gen Count: " + str(values.COUNT_TEMPLATE_GEN))
            statistics("Template Start Count: " + str(values.COUNT_TEMPLATE_START))
            statistics(
                "Template End Seed Count: " + str(values.COUNT_TEMPLATE_END_SEED)
            )
            statistics("Template End Count: " + str(values.COUNT_TEMPLATE_END))

        statistics("Paths Detected: " + str(values.COUNT_PATHS_DETECTED))
        statistics("Paths Explored: " + str(values.COUNT_PATHS_EXPLORED))
        statistics(
            "Paths Explored via Generation: " + str(values.COUNT_PATHS_EXPLORED_GEN)
        )
        statistics("Paths Skipped: " + str(values.COUNT_PATHS_SKIPPED))
        statistics("Paths Hit Patch Loc: " + str(values.COUNT_HIT_PATCH_LOC))
        statistics("Paths Hit Observation Loc: " + str(values.COUNT_HIT_BUG_LOG))
        statistics("Paths Hit Crash Loc: " + str(values.COUNT_HIT_CRASH_LOC))
        statistics("Paths Crashed: " + str(values.COUNT_HIT_CRASH))
        statistics("Component Count: " + str(values.COUNT_COMPONENTS))
        statistics("Component Count Gen: " + str(values.COUNT_COMPONENTS_GEN))
        statistics("Component Count Cus: " + str(values.COUNT_COMPONENTS_CUS))
        statistics("Gen Limit: " + str(values.DEFAULT_GEN_SEARCH_LIMIT))
        if is_error:
            error(
                "\n"
                + values.TOOL_NAME
                + " exited with an error after "
                + time_info[definitions.KEY_DURATION_TOTAL]
                + " minutes \n"
            )
        else:
            success(
                "\n"
                + values.TOOL_NAME
                + " finished successfully after "
                + time_info[definitions.KEY_DURATION_TOTAL]
                + " minutes \n"
            )


def emit_help():
    write("Usage: cpr [OPTIONS] " + definitions.ARG_CONF_FILE + "$FILE_PATH", WHITE)
    write("Options are:", WHITE)
    write(
        "\t"
        + definitions.ARG_TIME_DURATION
        + "\t| "
        + "specify the time duration for repair in minutes",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_ITERATION_COUNT
        + "\t| "
        + "limit number of iterations for repair",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_CEGIS_TIME_SPLIT
        + "\t| "
        + "specify time split ratio for CEGIS mode; explore:refine  in minutes(default=1:1)",
        WHITE,
    )
    write("\t" + definitions.ARG_DEBUG + "\t| " + "enable debugging information", WHITE)
    write(
        "\t"
        + definitions.ARG_OPERATION_MODE
        + "\t| "
        + "execution mode [0: sequential, 1: semi-paralle, 2: parallel] (default = 0)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_DISABLE_DISTANCE_CAL
        + "\t| "
        + "disable distance calculation (default=enabled)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_SELECTION_METHOD
        + "\t| "
        + "selection strategy [0: deterministic, 1: random] (default=0)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_DIST_METRIC
        + "\t| "
        + "distance metric [0: control-loc, 1: statement] (default=0)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_PATCH_TYPE
        + "\t| "
        + "patch type [0: concrete, 1: abstract] (default=0)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_REFINE_METHOD
        + "\t| "
        + "refine strategy [0: under-approx, 1: over-approx, 2: under-approx and over-approx, 3: none] (default=0)",
        WHITE,
    )
    write(
        "\t"
        + definitions.ARG_REDUCE_METHOD
        + "\t| "
        + "reduce method [0: cpr, 1: cegis] (default=0)",
        WHITE,
    )
