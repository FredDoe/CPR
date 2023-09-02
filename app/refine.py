from pysmt.shortcuts import is_sat, Not, And, TRUE
from pysmt.shortcuts import is_sat
from app import emitter, values, extractor, merger, oracle, generator, smt2


def refine_input_partition(
    path_condition, assertion, input_partition, is_multi_dimension
):
    input_constraints = generator.generate_constraint_for_input_partition(
        input_partition
    )
    path_constraints = And(path_condition, input_constraints)
    is_exist_check = And(path_constraints, Not(assertion))
    is_always_check = And(path_constraints, assertion)
    refined_partition_list = []
    if is_sat(is_always_check):
        if is_sat(is_exist_check):
            concrete_count = 1
            for parameter in input_partition:
                dimension = len(
                    range(
                        input_partition[parameter]["lower-bound"],
                        input_partition[parameter]["upper-bound"] + 1,
                    )
                )
                concrete_count = concrete_count * dimension
                if concrete_count > 1:
                    break
            if concrete_count == 1:
                return refined_partition_list
            partition_model = generator.generate_model(is_exist_check)
            partition_model, is_multi_dimension = extractor.extract_input_list(
                partition_model
            )
            partition_list = generator.generate_partition_for_input_space(
                partition_model, input_partition, is_multi_dimension
            )
            for partition in partition_list:
                if refined_partition_list:
                    refined_partition_list = (
                        refined_partition_list
                        + refine_input_partition(
                            path_condition, assertion, partition, is_multi_dimension
                        )
                    )
                else:
                    refined_partition_list = refine_input_partition(
                        path_condition, assertion, partition, is_multi_dimension
                    )
        else:
            refined_partition_list.append(input_partition)
    return refined_partition_list


def refine_patch_partition(
    path_constraint, patch_partition, p_specification, is_multi_dimension
):
    parameter_constraint = smt2.generate_constraint_for_patch_partition(patch_partition)
    path_feasibility = And(path_constraint, And(parameter_constraint, p_specification))
    refined_partition_list = []
    if is_sat(path_feasibility):
        concrete_count = 1
        for parameter in patch_partition:
            dimension = len(
                range(
                    patch_partition[parameter]["lower-bound"],
                    patch_partition[parameter]["upper-bound"] + 1,
                )
            )
            concrete_count = concrete_count * dimension
            if concrete_count > 1:
                break
        if concrete_count == 1:
            return refined_partition_list
        partition_model = generator.generate_model(path_feasibility)
        partition_model, is_multi_dimension = extractor.extract_parameter_list(
            partition_model
        )
        partition_list = generator.generate_partition_for_patch_space(
            partition_model, patch_partition, is_multi_dimension
        )
        for partition in partition_list:
            if refined_partition_list:
                refined_partition_list = (
                    refined_partition_list
                    + refine_patch_partition(
                        path_constraint, partition, p_specification, is_multi_dimension
                    )
                )
            else:
                refined_partition_list = refine_patch_partition(
                    path_constraint, partition, p_specification, is_multi_dimension
                )
    else:
        refined_partition_list = [patch_partition]
    return refined_partition_list


def refine_parameter_space(path_constraint, parameter_space, p_specification):
    refined_patch_space = list()
    is_multi_dimension = False
    for partition in parameter_space:
        if len(partition.keys()) > 1:
            is_multi_dimension = True
        refined_partition = refine_patch_partition(
            path_constraint, partition, p_specification, is_multi_dimension
        )
        if not refined_partition:
            continue
        if isinstance(refined_partition, list):
            for sub_partition in refined_partition:
                refined_patch_space.append(sub_partition)
        else:
            refined_patch_space.append(refined_partition)
    merged_refine_space = None
    if refined_patch_space:
        merged_refine_space = merger.merge_space(
            refined_patch_space, path_constraint, p_specification
        )
    return merged_refine_space


def refine_patch(p_specification, patch_formula, path_condition, index, patch_space):
    patch_score = 0
    is_under_approx = None
    is_over_approx = None
    refined_patch_space = patch_space
    if not patch_space:
        return None, index, patch_score, is_under_approx, is_over_approx

    if oracle.is_loc_in_trace(values.CONF_LOC_BUG):
        parameter_constraint = smt2.generate_constraint_for_patch_space(patch_space)
        patch_space_constraint = patch_formula
        if parameter_constraint:
            patch_space_constraint = And(patch_formula, parameter_constraint)
        path_constraint = And(path_condition, patch_space_constraint)
        negated_path_condition = values.NEGATED_PPC_FORMULA
        patch_score = 2
        refined_patch_space, is_under_approx, is_over_approx = refine_for_over_fit(
            patch_formula,
            path_condition,
            negated_path_condition,
            patch_space,
            p_specification,
        )

    else:
        patch_score = 1
        refined_patch_space = patch_space
    return refined_patch_space, index, patch_score, is_under_approx, is_over_approx


def refine_for_over_fit(
    patch_formula, path_condition, negated_path_condition, patch_space, p_specification
):
    refined_patch_space, is_under_approx = refine_for_under_approx(
        patch_formula, path_condition, patch_space, Not(p_specification)
    )
    if not refined_patch_space:
        return None, False, False
    is_over_approx = False
    if negated_path_condition and values.IS_PATCH_BOOL:
        refined_patch_space, is_over_approx = refine_for_over_approx(
            patch_formula, negated_path_condition, refined_patch_space, p_specification
        )
    return refined_patch_space, is_under_approx, is_over_approx


def refine_for_under_approx(
    patch_formula, path_condition, patch_space, p_specification
):
    parameter_constraint = smt2.generate_constraint_for_patch_space(patch_space)
    patch_space_constraint = patch_formula
    if parameter_constraint:
        patch_space_constraint = And(patch_formula, parameter_constraint)
    path_feasibility = And(path_condition, And(patch_space_constraint, p_specification))
    path_constraint = And(path_condition, patch_formula)
    if values.VALID_INPUT_SPACE:
        input_space_constraint = Not(
            smt2.generate_constraint_for_input_space(values.VALID_INPUT_SPACE)
        )
        path_feasibility = And(
            path_condition, And(patch_space_constraint, input_space_constraint)
        )
        path_constraint = And(
            And(path_condition, input_space_constraint), patch_formula
        )
    # invalid input range is used to check for violations

    refined_patch_space = patch_space
    is_under_approx = False
    if is_sat(path_feasibility):
        is_under_approx = True
        if values.DEFAULT_REFINE_METHOD in ["under-approx", "overfit"]:
            emitter.debug("refining for universal quantification")
            if parameter_constraint:
                refined_patch_space = refine_parameter_space(
                    path_constraint, patch_space, p_specification
                )
                is_under_approx = False
            else:
                refined_patch_space = None
    return refined_patch_space, is_under_approx


def refine_for_over_approx(patch_formula, path_condition, patch_space, p_specification):
    parameter_constraint = smt2.generate_constraint_for_patch_space(patch_space)
    patch_space_constraint = patch_formula
    if parameter_constraint:
        patch_space_constraint = And(patch_formula, parameter_constraint)
    path_feasibility = And(path_condition, And(patch_space_constraint, p_specification))
    path_constraint = And(path_condition, patch_formula)
    if values.VALID_INPUT_SPACE:
        input_space_constraint = smt2.generate_constraint_for_input_space(
            values.VALID_INPUT_SPACE
        )
        path_feasibility = And(
            path_condition, And(patch_space_constraint, input_space_constraint)
        )
        path_constraint = And(
            And(path_condition, input_space_constraint), patch_formula
        )
    refined_patch_space = patch_space
    is_over_approx = False
    if is_sat(path_feasibility):
        is_over_approx = True
        if values.DEFAULT_REFINE_METHOD in ["over-approx", "overfit"]:
            emitter.debug("refining for existential quantification")
            if parameter_constraint:
                refined_patch_space = refine_parameter_space(
                    path_constraint, patch_space, p_specification
                )
                is_over_approx = False
            else:
                refined_patch_space = None
    return refined_patch_space, is_over_approx
