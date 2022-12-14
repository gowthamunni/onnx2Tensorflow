import random
random.seed(0)
import numpy as np
np.random.seed(0)
import tensorflow as tf
import onnx_graphsurgeon as gs
from onnx2tf.utils.common_functions import (
    get_constant_or_variable,
    print_node_info,
    inverted_operation_enable_disable,
    make_tf_node_info,
)


@print_node_info
@inverted_operation_enable_disable
def make_node(
    *,
    graph_node: gs.Node,
    tf_layers_dict: dict,
    **kwargs: dict,
):
    """Einsum

    Parameters
    ----------
    graph_node: gs.Node
        graph_surgeon Node

    tf_layers_dict: dict
        optype, shape, dtype, tensorflow graph
    """
    before_op_output_shape_trans = True
    for graph_node_input in graph_node.inputs:
        before_op_output_shape_trans_n = \
            tf_layers_dict.get(graph_node_input.name, {}).get('before_op_output_shape_trans', True)
        before_op_output_shape_trans = \
            before_op_output_shape_trans and before_op_output_shape_trans_n

    inputs = []
    for graph_node_input in graph_node.inputs:
        graph_node_input_perm = get_constant_or_variable(
            graph_node_input,
            before_op_output_shape_trans,
        )
        input_tensor = tf_layers_dict[graph_node_input_perm.name]['tf_node'] \
            if isinstance(graph_node_input_perm, gs.Variable) else graph_node_input_perm
        inputs.append(input_tensor)
    graph_node_output: gs.Variable = graph_node.outputs[0]
    shape = graph_node_output.shape
    dtype = graph_node_output.dtype

    equation = graph_node.attrs['equation']

    # Preserving Graph Structure (Dict)
    tf_layers_dict[graph_node_output.name] = {
        'optype': graph_node.op,
        'shape': shape,
        'dtype': dtype,
    }

    # Generation of TF OP
    tf_layers_dict[graph_node_output.name]['tf_node'] = \
        tf.einsum(
            equation,
            *inputs,
            name=graph_node.name,
        )

    # Generation of Debug Info
    tf_inputs = {f"input{idx}": input for idx, input in enumerate(inputs)}
    tf_inputs['equation'] = equation
    tf_layers_dict[graph_node_output.name]['tf_node_info'] = \
        make_tf_node_info(
            node_info={
                'tf_op_type': tf.einsum,
                'tf_inputs': tf_inputs,
                'tf_outputs': {
                    'output': tf_layers_dict[graph_node_output.name]['tf_node'],
                },
            }
        )
