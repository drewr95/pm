import functools
import os
import textwrap

import click.testing
import pycparser.c_ast
import pycparser.c_generator

import epcpm.parametermodel
import epcpm.parameterstoc


def disabled_test_exploration():
    path = os.path.join(os.path.dirname(__file__), 'example_parameters.json')

    runner = click.testing.CliRunner()
    runner.isolated_filesystem()
    result = runner.invoke(
        epcpm.parameterstoc.cli,
        [
            '--parameters', path,
        ],
    )

    print(result.output)

    assert result.exit_code == 0


def test_exploration():
    path = os.path.join(os.path.dirname(__file__), 'example_parameters.json')

    with open(path) as f:
        epcpm.parameterstoc._cli(parameters=f)


def test_pycparser_exploration_parse():
    sample = '''
    typedef int int16_t;
    typedef int uint16_t;

    enum EnumName
    {
        one=1,
        two=2
    };
    typedef enum EnumName EnumTypedefName;

    struct StructName
    {
        int16_t a;
        uint16_t b;
    };
    typedef struct StructName StructTypedefName;
    '''

    parser = pycparser.CParser()
    ast = parser.parse(sample)

    generator = pycparser.c_generator.CGenerator()

    generator.visit(ast)


def test_pycparser_exploration_wrapped():
    top_level = []

    top_level.extend(epcpm.parameterstoc.enum(
        name='EnumName',
        enumerators=(
            ('a', 1),
            ('b', 2),
        ),
    ))

    top_level.extend(epcpm.parameterstoc.struct(
        name='StructName',
        members=(
            ('int16_t', 'a', None),
            ('uint16_t', 'b', None),
        )
    ))

    ast = pycparser.c_ast.FileAST(top_level)

    generator = pycparser.c_generator.CGenerator()

    s = generator.visit(ast)
    assert s == textwrap.dedent('''\
    enum EnumName_e {a = 1, b = 2};
    typedef enum EnumName_e EnumName_t;
    struct StructName_s
    {
      int16_t a;
      uint16_t b;
    };
    typedef enum StructName_s StructName_t;
    ''')


def test_single_layer_group_to_c():
    group = epcpm.parametermodel.Group(
        name='Group Name',
    )

    children = [
        epcpm.parametermodel.Parameter(
            name='Parameter A',
        ),
        epcpm.parametermodel.Parameter(
            name='Parameter B',
        ),
        epcpm.parametermodel.Parameter(
            name='Parameter C',
        ),
    ]

    for child in children:
        group.append_child(child)

    top_level = epcpm.parameterstoc.build_ast(group)
    ast = pycparser.c_ast.FileAST(top_level)
    generator = pycparser.c_generator.CGenerator()
    s = generator.visit(ast)

    assert s == textwrap.dedent('''\
        struct GroupName_s
        {
          int16_t parameterA;
          int16_t parameterB;
          int16_t parameterC;
        };
        typedef enum GroupName_s GroupName_t;
        ''')


def test_nested_group_to_c():
    inner_group = epcpm.parametermodel.Group(
        name='Inner Group Name',
    )

    children = [
        epcpm.parametermodel.Parameter(
            name='Parameter D',
        ),
        epcpm.parametermodel.Parameter(
            name='Parameter E',
        ),
    ]

    for child in children:
        inner_group.append_child(child)

    outer_group = epcpm.parametermodel.Group(
        name='Outer Group Name',
    )

    children = [
        epcpm.parametermodel.Parameter(
            name='Parameter A',
        ),
        inner_group,
        epcpm.parametermodel.Parameter(
            name='Parameter B',
        ),
        epcpm.parametermodel.Parameter(
            name='Parameter C',
        ),
    ]

    for child in children:
        outer_group.append_child(child)

    ast = pycparser.c_ast.FileAST(epcpm.parameterstoc.build_ast(outer_group))
    generator = pycparser.c_generator.CGenerator()
    s = generator.visit(ast)

    assert s == textwrap.dedent('''\
        struct InnerGroupName_s
        {
          int16_t parameterD;
          int16_t parameterE;
        };
        typedef enum InnerGroupName_s InnerGroupName_t;
        struct OuterGroupName_s
        {
          int16_t parameterA;
          InnerGroupName_t innerGroupName;
          int16_t parameterB;
          int16_t parameterC;
        };
        typedef enum OuterGroupName_s OuterGroupName_t;
        ''')
