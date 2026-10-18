"""
BioPulse-Z Pure-ONNX Model Generator (Cross-Version Compatible)
Constructs a native clinical ONNX computational graph with pinned IR and Opset versions.
"""
import numpy as np
import onnx
from onnx import helper, TensorProto

def create_clinical_onnx_model(output_path="biopulse_sepsis.onnx"):
    print("[*] Constructing native clinical ONNX computational graph...")

    # Input: float_input [batch_size, 6]
    # Features: [HR, SysBP, DiaBP, RespRate, SpO2, ShockIndex]
    float_input = helper.make_tensor_value_info("float_input", TensorProto.FLOAT, [None, 6])
    probabilities = helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, [None, 2])

    # Model Weights & Biases (Simulating trained ensemble coefficients)
    weights_val = np.array([[0.045], [-0.040], [-0.015], [0.080], [-0.090], [2.100]], dtype=np.float32)
    bias_val = np.array([4.20], dtype=np.float32)

    weights_tensor = helper.make_tensor("weights", TensorProto.FLOAT, [6, 1], weights_val.flatten())
    bias_tensor = helper.make_tensor("bias", TensorProto.FLOAT, [1], bias_val.flatten())
    one_tensor = helper.make_tensor("one_const", TensorProto.FLOAT, [1], [1.0])

    # Graph Operations: MatMul -> Add (logits) -> Sigmoid -> Sub -> Concat
    matmul_node = helper.make_node("MatMul", ["float_input", "weights"], ["matmul_out"])
    add_node = helper.make_node("Add", ["matmul_out", "bias"], ["logits"])
    sigmoid_node = helper.make_node("Sigmoid", ["logits"], ["p_decomp"])
    sub_node = helper.make_node("Sub", ["one_const", "p_decomp"], ["p_stable"])
    concat_node = helper.make_node("Concat", ["p_stable", "p_decomp"], ["probabilities"], axis=1)

    graph_def = helper.make_graph(
        nodes=[matmul_node, add_node, sigmoid_node, sub_node, concat_node],
        name="BioPulseZ_Telum_Graph",
        inputs=[float_input],
        outputs=[probabilities],
        initializer=[weights_tensor, bias_tensor, one_tensor]
    )

    opset = helper.make_opsetid("", 13)
    model_def = helper.make_model(
        graph_def,
        producer_name="BioPulse-Z-Architecture",
        opset_imports=[opset],
        ir_version=9
    )

    onnx.checker.check_model(model_def)
    onnx.save(model_def, output_path)
    print(f"[+] Successfully generated ONNX model: {output_path} (IR: 9, Opset: 13)")

if __name__ == "__main__":
    create_clinical_onnx_model()