from lat.codegen.emitters import (
    BINARY_OPS,
    UNARY_OPS,
    READ_OPS,
    WRITE_OPS,
    BytecodeEmitter,
)


def test_binary_ops_mappings():
    assert BINARY_OPS["+"] == "ADD"
    assert BINARY_OPS["-"] == "SUB"
    assert BINARY_OPS["*"] == "MUL"
    assert BINARY_OPS["/"] == "DIV"
    assert BINARY_OPS["=="] == "EQUAL"
    assert BINARY_OPS["&&"] == "AND"
    assert BINARY_OPS["||"] == "OR"


def test_unary_ops_mappings():
    assert UNARY_OPS["-"] == ["PUSHI -1", "MUL"]
    assert UNARY_OPS["!"] == ["NOT"]
    assert UNARY_OPS["++"] == ["PUSHI 1", "ADD"]


def test_read_ops_mappings():
    assert READ_OPS["integer"] == "READI"
    assert READ_OPS["float"] == "READF"
    assert READ_OPS["filum"] == "READS"


def test_write_ops_mappings():
    assert WRITE_OPS["integer"] == "WRITEI"
    assert WRITE_OPS["float"] == "WRITEF"
    assert WRITE_OPS["filum"] == "WRITES"


def test_emitter_creation():
    emitter = BytecodeEmitter()
    assert emitter.output == []
    assert emitter.label_counter == 0


def test_emit():
    emitter = BytecodeEmitter()
    emitter.emit("PUSHI 42")
    assert emitter.output == ["PUSHI 42"]


def test_emit_lines():
    emitter = BytecodeEmitter()
    emitter.emit_lines("PUSHI 1\nADD\n")
    assert emitter.output == ["PUSHI 1", "ADD"]


def test_new_label():
    emitter = BytecodeEmitter()
    label1 = emitter.new_label()
    label2 = emitter.new_label("LOOP")
    assert label1 == "L1"
    assert label2 == "LOOP2"
    assert emitter.label_counter == 2


def test_emit_push_integer():
    emitter = BytecodeEmitter()
    emitter.emit_push("integer", 42)
    assert emitter.output == ["PUSHI 42"]


def test_emit_push_float():
    emitter = BytecodeEmitter()
    emitter.emit_push("float", 3.14)
    assert emitter.output == ["PUSHF 3.14"]


def test_emit_push_filum():
    emitter = BytecodeEmitter()
    emitter.emit_push("filum", '"hello"')
    assert emitter.output == ['PUSHS "hello"']


def test_emit_push_unknown():
    emitter = BytecodeEmitter()
    emitter.emit_push("unknown", "value")
    assert emitter.output == ["PUSHI 0"]


def test_emit_load_global():
    emitter = BytecodeEmitter()
    emitter.emit_load("global", 5)
    assert emitter.output == ["PUSHGP", "LOAD 5"]


def test_emit_load_local():
    emitter = BytecodeEmitter()
    emitter.emit_load("local", 3)
    assert emitter.output == ["PUSHFP", "LOAD 3"]


def test_emit_load_param():
    emitter = BytecodeEmitter()
    emitter.emit_load("param", 1)
    assert emitter.output == ["PUSHFP", "LOAD 1"]


def test_emit_load_unknown_scope():
    emitter = BytecodeEmitter()
    try:
        emitter.emit_load("unknown", 0)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Unknown scope" in str(e)


def test_emit_store_global():
    emitter = BytecodeEmitter()
    emitter.emit_store("global", 2)
    assert emitter.output == ["STOREG 2"]


def test_emit_store_local():
    emitter = BytecodeEmitter()
    emitter.emit_store("local", 4)
    assert emitter.output == ["STOREL 4"]


def test_emit_store_param():
    emitter = BytecodeEmitter()
    emitter.emit_store("param", 1)
    assert emitter.output == ["PUSHFP", "STORE 1"]


def test_emit_binop():
    emitter = BytecodeEmitter()
    emitter.emit_binop("+")
    assert emitter.output == ["ADD"]


def test_emit_binop_unknown():
    emitter = BytecodeEmitter()
    emitter.emit_binop("CUSTOM")
    assert emitter.output == ["CUSTOM"]


def test_emit_unaryop():
    emitter = BytecodeEmitter()
    emitter.emit_unaryop("-")
    assert emitter.output == ["PUSHI -1", "MUL"]


def test_emit_read():
    emitter = BytecodeEmitter()
    emitter.emit_read("integer")
    assert emitter.output == ["READI"]


def test_emit_write():
    emitter = BytecodeEmitter()
    emitter.emit_write("float")
    assert emitter.output == ["WRITEF"]


def test_emit_main_entry():
    emitter = BytecodeEmitter()
    emitter.emit_main_entry()
    assert emitter.output == ["start", "PUSHA main", "CALL", "stop"]


def test_emit_function_prologue():
    emitter = BytecodeEmitter()
    emitter.emit_function_prologue("main", 2)
    assert emitter.output == ["main:", "PUSHN 2"]


def test_emit_function_prologue_with_params():
    emitter = BytecodeEmitter()
    emitter.emit_function_prologue("func", 0, 2, params_to_locals=True)
    expected = [
        "func:",
        "PUSHI 0",
        "PUSHFP",
        "LOAD -2",
        "STOREL 0",
        "PUSHI 0",
        "PUSHFP",
        "LOAD -1",
        "STOREL 1",
    ]
    assert emitter.output == expected


def test_to_string():
    emitter = BytecodeEmitter()
    emitter.emit("start")
    emitter.emit("stop")
    result = emitter.to_string()
    assert result == "start\nstop\n"
