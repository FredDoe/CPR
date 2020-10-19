from main.concolic import run_concolic_execution, select_new_input
from main.synthesis import load_specification, Program
from pathlib import Path
from typing import List, Dict, Tuple
from main import emitter, values, distance, oracle, parallel, generator, extractor, utilities, concolic
import time
import sys
import operator
import numpy


def reduce(patch_list: List[Dict[str, Program]], path_to_concolic_exec_result: str,
           assertion) -> List[Tuple[str, Program]]:  # TODO
    # Reduces the set of patch candidates based on the current path constraint
    # Iterate over patches and check if they still hold based on path constraint.
    emitter.normal("\tupdating patch pool")
    updated_patch_list = []
    path_constraint_file_path = str(path_to_concolic_exec_result) + "/test000001.smt2"
    expr_log_path = str(path_to_concolic_exec_result) + "/expr.log"
    path_condition = extractor.extract_assertion(path_constraint_file_path)
    if values.CONF_PATCH_TYPE == values.OPTIONS_PATCH_TYPE[1]:
        result_list = parallel.refine_patches_parallel(patch_list, path_condition, assertion)
        if not result_list:
            emitter.error("\tsomething went wrong with patch validation")
            utilities.error_exit()
        for result in result_list:
            refined_space, index = result
            if refined_space:
                updated_patch_list.append(patch_list[index])
                patch = patch_list[index]
                patch_constraint = extractor.extract_constraints_from_patch(patch)
                patch_constraint_str = patch_constraint.serialize()
                patch_index = utilities.get_hash(patch_constraint_str)
                values.LIST_PATCH_CONSTRAINTS[patch_index] = refined_space
            else:
                # emitter.debug("Removing Patch", patch_list[index])
                emitter.emit_patch(patch_list[index], message="\t\tRemoving Patch: ")
    else:
        result_list = parallel.validate_patches_parallel(patch_list, path_condition, assertion)
        if not result_list:
            emitter.error("\tsomething went wrong with patch validation")
            utilities.error_exit()
        for result in result_list:
            refined_space, index = result
            if refined_space:
                updated_patch_list.append(patch_list[index])
                patch = patch_list[index]
                patch_constraint = extractor.extract_constraints_from_patch(patch)
                patch_constraint_str = patch_constraint.serialize()
                patch_index = utilities.get_hash(patch_constraint_str)
                values.LIST_PATCH_CONSTRAINTS[patch_index] = refined_space
            else:
                # emitter.debug("Removing Patch", patch_list[index])
                emitter.emit_patch(patch_list[index], message="\t\tRemoving Patch: ")

    return updated_patch_list


def print_patch_list(patch_list):
    template_count = 0
    emitter.sub_title("List of Top " + str(values.DEFAULT_PATCH_RANK_LIMIT) + " Correct Patches")
    if not patch_list:
        emitter.warning("\t[warning] unable to generate any patch")
        return
    for patch in patch_list:
        template_count = template_count + 1
        emitter.sub_sub_title("Patch #" + str(template_count))
        emitter.emit_patch(patch, message="\t\t")
        if values.CONF_PATCH_TYPE == values.OPTIONS_PATCH_TYPE[1]:
            patch_constraint = extractor.extract_constraints_from_patch(patch)
            patch_constraint_str = patch_constraint.serialize()
            patch_index = utilities.get_hash(patch_constraint_str)
            constant_space = values.LIST_PATCH_CONSTRAINTS[patch_index]
            for constant_name in constant_space:
                constant_info = constant_space[constant_name]
                lower_bound = str(constant_info['lower-bound'])
                upper_bound = str(constant_info['upper-bound'])
                emitter.highlight("\t\tRange: " + lower_bound + " <= " + constant_name + " <= " + upper_bound)
                concrete_count = len(range(int(lower_bound), int(upper_bound) + 1))
                emitter.highlight("\t\tCount: " + str(concrete_count))
        if template_count == values.DEFAULT_PATCH_RANK_LIMIT:
            break


def count_concrete_patches(patch_list):
    con_count = 0
    for patch in patch_list:
        patch_constraint = extractor.extract_constraints_from_patch(patch)
        patch_constraint_str = patch_constraint.serialize()
        patch_index = utilities.get_hash(patch_constraint_str)
        constant_space = values.LIST_PATCH_CONSTRAINTS[patch_index]
        for constant_name in constant_space:
            constant_info = constant_space[constant_name]
            lower_bound = str(constant_info['lower-bound'])
            upper_bound = str(constant_info['upper-bound'])
            tmp_count = len(range(int(lower_bound), int(upper_bound) + 1))
            con_count = con_count + tmp_count
    return con_count


def rank_patches(patch_list):
    filtered_list = []
    # rank first based on coverage
    for patch in patch_list:
        patch_constraint_str = extractor.extract_constraints_from_patch(patch).serialize()
        patch_index = utilities.get_hash(patch_constraint_str)
        patch_score = values.LIST_PATCH_SCORE[patch_index]
        patch_len = 10000 - len(patch_constraint_str)
        filtered_list.append((patch, patch_score, patch_len))

    ranked_list = sorted(filtered_list, key=operator.itemgetter(1, 2))
    ranked_list.reverse()
    patch_list = numpy.array(ranked_list)[:,0]
    return list(patch_list)


def run(project_path, program_path):
    emitter.title("Repairing Program")
    ## Generate all possible solutions by running the synthesizer.

    emitter.note("\tconfiguration.is_crash:" + str(values.IS_CRASH))
    emitter.note("\tconfiguration.assertion:" + str(values.SPECIFICATION))
    emitter.note("\tconfiguration.generation_limit:" + str(values.DEFAULT_GEN_SEARCH_LIMIT))
    emitter.note("\tconfiguration.max_bound:" + str(values.DEFAULT_UPPER_BOUND))
    emitter.note("\tconfiguration.low_bound:" + str(values.DEFAULT_LOWER_BOUND))
    emitter.note("\tconfiguration.stack_size:" + str(sys.getrecursionlimit()))

    time_check = time.time()
    P = generator.generate_patch_set(project_path)
    for patch in P:
        patch_constraint_str = extractor.extract_constraints_from_patch(patch).serialize()
        patch_index = utilities.get_hash(patch_constraint_str)
        if patch_index in values.LIST_PATCH_SCORE:
            emitter.warning("\tcollision detected in patch score map")
        values.LIST_PATCH_SCORE[patch_index] = 0
        values.LIST_PATCH_CONSTRAINTS[patch_index] = generator.generate_constraints_on_constants(patch)

    if values.CONF_PATCH_TYPE == values.OPTIONS_PATCH_TYPE[1]:
        values.COUNT_PATCH_START = count_concrete_patches(P)
    else:
        values.COUNT_PATCH_START = len(P)

    duration = format((time.time() - time_check) / 60, '.3f')
    values.TIME_TO_GENERATE = str(duration)
    emitter.sub_title("Evaluating Patch Pool")
    satisfied = len(P) <= 1
    iteration = 0
    assertion = values.SPECIFICATION
    test_output_list = values.CONF_TEST_OUTPUT
    binary_dir_path = "/".join(program_path.split("/")[:-1])

    while not satisfied and len(P) > 1:
        iteration = iteration + 1
        values.ITERATION_NO = iteration
        emitter.sub_sub_title("Iteration: " + str(iteration))
        ## Pick new input and patch candidate for next concolic execution step.
        argument_list = values.ARGUMENT_LIST
        second_var_list = values.SECOND_VAR_LIST
        if oracle.is_loc_in_trace(values.CONF_LOC_PATCH):
            values.LIST_GENERATED_PATH = generator.generate_symbolic_paths(values.LIST_PPC)
        gen_arg_list, gen_var_list, P = select_new_input(argument_list, second_var_list, P)  # TODO (later) patch candidate missing
        if not P:
            emitter.warning("\t\t[warning] unable to generate a patch")
            break
        elif not gen_arg_list and not gen_var_list:
            emitter.warning("\t\t[warning] no more paths to generate new input")
            break
        assert gen_arg_list  # there should be a concrete input
        # print(">> new input: " + str(gen_arg_list))

        ## Concolic execution of concrete input and patch candidate to retrieve path constraint.
        exit_code = run_concolic_execution(program_path + ".bc", gen_arg_list, gen_var_list)
        assert exit_code == 0

        # Checks for the current coverage.
        satisfied = utilities.check_budget()

        # check if new path hits patch location / fault location
        if not oracle.is_loc_in_trace(values.CONF_LOC_PATCH):
            continue
        if not values.IS_CRASH and not oracle.is_loc_in_trace(values.CONF_LOC_BUG):
            continue

        distance.update_distance_map()
        ## Reduces the set of patch candidates based on the current path constraint
        P = reduce(P, Path(binary_dir_path + "/klee-last/").resolve(), assertion)
        emitter.note("\t\t|P|=" + str(len(P)))

    if not P:
        values.COUNT_PATCH_END = len(P)
        emitter.warning("\t\t[warning] unable to generate a patch")
    else:
        ranked_patch_list = rank_patches(P)
        print_patch_list(ranked_patch_list)
        if values.CONF_PATCH_TYPE == values.OPTIONS_PATCH_TYPE[1]:
            values.COUNT_PATCH_END = count_concrete_patches(ranked_patch_list)
        else:
            values.COUNT_PATCH_END = len(ranked_patch_list)



def concolic_exploration(program_path):
    while not satisfied and len(patch_list) > 1:
        patch_list = values.LIST_PATCHES
        iteration = iteration + 1
        values.ITERATION_NO = iteration
        emitter.sub_sub_title("Iteration: " + str(iteration))

        ## Pick new input and patch candidate for next concolic execution step.
        argument_list = values.ARGUMENT_LIST
        second_var_list = values.SECOND_VAR_LIST
        if oracle.is_loc_in_trace(values.CONF_LOC_PATCH):
            values.LIST_GENERATED_PATH = generator.generate_symbolic_paths(values.LIST_PPC)
        gen_arg_list, gen_var_list, patch_list = concolic.select_new_input(argument_list, second_var_list,
                                                                           patch_list)  # TODO (later) patch candidate missing

        if not patch_list:
            emitter.warning("\t\t[warning] unable to generate a patch")
            break
        elif not gen_arg_list and not gen_var_list:
            emitter.warning("\t\t[warning] no more paths to generate new input")
            break
        assert gen_arg_list  # there should be a concrete input
        # print(">> new input: " + str(gen_arg_list))

        ## Concolic execution of concrete input and patch candidate to retrieve path constraint.
        exit_code = concolic.run_concolic_execution(program_path + ".bc", gen_arg_list, gen_var_list)
        assert exit_code == 0

        # Checks for the current coverage.
        satisfied = utilities.check_budget()

        # check if new path hits patch location / fault location
        if not oracle.is_loc_in_trace(values.CONF_LOC_PATCH):
            continue
        if not values.IS_CRASH and not oracle.is_loc_in_trace(values.CONF_LOC_BUG):
            continue
        distance.update_distance_map()
