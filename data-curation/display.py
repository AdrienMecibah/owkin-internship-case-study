import pandas as pd
import json
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State


NON_COMPLIANT_COLOR = '#D22B2B'


def display_assessment(assessment, dataset=None):

    # loading files
    if type(assessment) == str:
        original_assessment_file = assessment
        with open(assessment, 'r') as f:
            assessment = json.load(f)
    else:
        original_assessment_file = None
        pass # let's assume the assessment is correct in shape 
    if dataset is not None:
        if type(dataset) == str:
            df = pd.read_csv(dataset, sep=';')
        else:
            df = dataset
    else:
        df = None

    # counting errors per variable and highlighting errors in table
    data_table_highlights = list()
    errors_per_variable = dict()
    nb_errors = 0
    for entry in assessment['non_compliant_entries']:
        for error in entry['errors']:
            if error['variable'] is not None:
                data_table_highlights.append((error['variable'], entry['row'][error['variable']]))
                errors_per_variable[error['variable']] = errors_per_variable.get(error['variable'], 0) + 1
                nb_errors += 1


    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # app layout
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Dataset quality assessment'), className='mb-4')
        ]),
        dbc.Row([]) if original_assessment_file is None else dbc.Row([
            html.H5(f'Opening assessment file "{original_assessment_file}"'),
        ]),
        dbc.Row(list(), style={'height': '50px'}),
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dcc.Checklist(
                        id = 'show-non-compliant',
                        options = [dict(label=' Show Non-Compliant Variables Only', value='show')],
                        value = list(),
                        inline = True,
                    ),
                    dcc.Checklist(
                        id = 'sort-variables',
                        options = [dict(label=' Sort Variables', value='sort')],
                        value = list(),
                        inline = True,
                    ),
                ]),
            ], width=6, className='mb-4'),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='bar-graph')
            ], width=9),
            dbc.Col([
                dcc.Graph(id='donut-chart')
            ], width=3),
        ]),
        dbc.Row(list(), style={'height': '50px'}),
        dbc.Row([
            dbc.Col([
                html.H5('Statistics'),
                html.P(f'Number of variables: {assessment["nb_variables"]}'),
                html.P(f'Number of entries: {assessment["nb_entries"]}'),
                html.P(f'Number of values: {assessment["nb_values"]}'),
                html.P(f'Total Non-Compliant variables: {len(assessment["non_compliant_variables"])} ({len(assessment["non_compliant_variables"])/assessment["nb_variables"]*100:.2f}%)'),
                html.P(f'Total Non-Compliant entries: {len(assessment["non_compliant_entries"])} ({len(assessment["non_compliant_entries"])/assessment["nb_entries"]*100:.2f}%)'),
                html.P(f'Total Non-Compliant values: {nb_errors} ({nb_errors/assessment["nb_values"]*100:.2f}%)'),
            ], width=3,),
            dbc.Col([]) if df is None else dbc.Col([
                dash_table.DataTable(
                    id = 'table',
                    columns = [dict(name=i, id=i) for i in df.columns],
                    data = df.to_dict('records'),
                    page_size = 10,
                    style_table = dict(overflowX='auto'),
                    style_cell = dict(
                        height = 'auto',
                        minWidth = '150px', 
                        width = '150px',
                        maxWidth = '150px',
                        whiteSpace = 'normal',
                    ),
                    style_data_conditional = [
                        {
                            'if': {
                                'filter_query': f'{{{variable}}} = "{value}"', 
                                'column_id': variable,
                            },
                            'color': 'red',
                        }
                        for variable, value in data_table_highlights
                    ]
                )
            ], width=9)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Modal(
                    [
                        dbc.ModalHeader('Entry errors'),
                        dbc.ModalBody(id='modal-body'),
                        dbc.ModalFooter(
                            dbc.Button('Close', id='close', className='ml-auto')
                        )
                    ],
                    id = 'modal',
                    is_open = False
                )
            ])
        ])
    ])

    # Combined callback to update the graph and modal
    @app.callback(
        [Output('bar-graph', 'figure'),
         Output('modal', 'is_open'),
         Output('modal-body', 'children'),
         Output('donut-chart', 'figure')],
        [Input('show-non-compliant', 'value'),
         Input('sort-variables', 'value'),
         Input('bar-graph', 'clickData'),
         Input('close', 'n_clicks')],
        [State('modal', 'is_open'),
         State('show-non-compliant', 'value'),
         State('sort-variables', 'value')]
    )
    def update_content(show_non_compliant, sort_variables, clickData, close_clicks, is_open, prev_show_non_compliant, prev_sort_variables):

        if 'show' in show_non_compliant:
            variables = list(assessment['non_compliant_variables'])
        else:
            variables = assessment['all_variables']
        if 'sort' in sort_variables:
            variables = list(sorted(variables))

        bar_figure = {
            'data': [
                go.Bar(
                    x = variables,
                    y = [errors_per_variable.get(variable, 0) for variable in variables],
                    text = [errors_per_variable.get(variable, 0) for variable in variables],
                    textposition = 'auto',
                    customdata = [assessment['non_compliant_variables'].get(var, 0) for var in variables],
                    hovertemplate = '<b>%{x}</b><br>Non-Compliant Rows: %{customdata}<extra></extra>',
                    marker = dict(color=NON_COMPLIANT_COLOR)
                )
            ],
            'layout': go.Layout(
                title='Non-Compliant Variables' if 'show' in show_non_compliant else 'All Variables',
                xaxis={'title': '<br>Variables'},
                yaxis={'title': 'Count of Non-Compliant Rows'},
            )
        }

        donut_figure = {
            'data': [
                go.Pie(
                    values = [assessment['nb_entries']-len(assessment['non_compliant_entries']), len(assessment['non_compliant_entries']), ],
                    labels = ['Compliant entries', 'Non-compliant entries', ],
                    marker = dict(colors=['grey', NON_COMPLIANT_COLOR]),
                    hole = 0.3,
                    textinfo = 'label+percent'
                )
            ],
            'layout': go.Layout(
                title = 'Entries',
                showlegend = False,
                margin = dict(b=0, l=0, r=0),
            )
        }

        # handle modal updates
        modal_body = list()
        if dash.callback_context.triggered and dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'bar-graph':
            variable = clickData['points'][0]['x']
            modal_body = [html.H5(f'Entries with non compliant "{variable}"')] 
            for entry in assessment['non_compliant_entries']:
                for error in entry['errors']:
                    if error['variable'] == variable:
                        modal_body.append(html.P([
                            html.Span(f'Entry {entry["index"]+1} : '), 
                            html.Span(f'{entry["row"][variable]}', style=dict(color='red')),
                            html.Span(f' : {error["message"]}'), 
                        ]))
            is_open = True
        elif dash.callback_context.triggered and dash.callback_context.triggered[0]['prop_id'].split('.')[0] == 'close':
            is_open = False
        elif (show_non_compliant != prev_show_non_compliant) or (sort_variables != prev_sort_variables):
            is_open = False

        return bar_figure, is_open, modal_body, donut_figure

    app.run_server(debug=True)
