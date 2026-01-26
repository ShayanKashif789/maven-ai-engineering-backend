import ast
import operator as op
import logging
from typing import Dict, Any
from langchain.tools import tool
from assignments.AgenticQASystem3.tools.schemas import CalculatorInput


logger = logging.getLogger(__name__)

ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,  # Support for negative numbers like -5
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        return node.value

    elif isinstance(node, ast.BinOp):
        operator_func = ALLOWED_OPERATORS.get(type(node.op))
        if not operator_func:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return operator_func(
            _safe_eval(node.left),
            _safe_eval(node.right)
        )

    elif isinstance(node, ast.UnaryOp):
        operator_func = ALLOWED_OPERATORS.get(type(node.op))
        if not operator_func:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return operator_func(_safe_eval(node.operand))

    else:
        raise ValueError(f"Invalid expression node: {type(node.__class__.__name__)}")


@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> Dict[str, Any]:
    """
    Perform exact mathematical calculations.
    Use this for any numerical operations to ensure 100% accuracy.
    """
    try:
        # Clean the expression of any accidental extra quotes the LLM might send
        expression = expression.strip().strip("'").strip('"')
        
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval(parsed.body)

        return {
            "status": "success",
            "tool": "calculator",
            "output": result,
            "error": None
        }

    except Exception as e:
        logger.warning(f"Calculator failed for expression '{expression}': {str(e)}")
        return {
            "status": "error",
            "tool": "calculator",
            "output": None,
            "error": {
                "message": str(e),
                "type": type(e).__name__
            }
        }