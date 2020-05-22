// Load the Visualization API and the corechart package.
$(function () {
    google.charts.load('current', {'packages': ['corechart']});
});

// Set a callback to run when the Google Visualization API is loaded.
$(function () {
    google.charts.setOnLoadCallback(drawChart);
});

// Callback that creates and populates a data table,
// instantiates the pie chart, passes in the data and
// draws it.


function drawChart() {
    if ($('#declarations').length) {
        var dataDeclarationsPieChart = google.visualization.arrayToDataTable([
            ['Тип', 'Кількість'],
            ['Зарплата', 2016],
            ['Роялтi', 1000],
            ['Автобiзнес', 1170],
            ['Продаж нерухомостi', 660],
        ]);



        var dataCashAssetsPieChart = google.visualization.arrayToDataTable([
            ['Тип', 'Кількість'],
            ['Вклади', 2016],
            ['Готівка', 1000],
            ['Інше', 1170],
        ]);

        // var data2 = new google.visualization.DataTable();
        // data2.addColumn('string', 'Рік');
        // data2.addColumn('number', 'Доходи декларанта');
        // data2.addColumn('number', 'Доходи родини');
        // data2.addColumn('number', 'Витрати декларанта');
        //
        // data2.addRows([
        //     ['2011', 1000, 400, 1230],
        //     ['2012', 1170, 560, 1000],
        //     ['2014', 660, 1120, 1450,],
        //     ['2016', 1030, 1640, 900,],
        //     ['2016', 2030, 1238, 600,],
        //     ['2017', 3219, 1022, 2000,],
        //     ['2018', 1319, 622, 1700,],
        //     ['2019', 1319, 622, 1700,],
        // ]);

        // Set chart options
        var options = {
            height: '300',
            lineWidth: '3',
            pointSize: '10',
            chartArea: {left: '10%', width: '80%'},
            colors: ['#4ead33', '#f39200'],
            backgroundColor: 'transparent',
            hAxis: {
                baselineColor: '#f2f2f',
                // baselineColor: 'red',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,
                },
                gridlines: {
                    color: 'transparent'
                }
            },
            vAxis: {
                baselineColor: '#f2f2f2',
                // baselineColor: 'red',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,
                },
                gridlines: {
                    color: 'transparent'
                },
                format: 'short',
                title: $("#cash-assets").data("chart-title"),
            },
            legend: {
                position: 'bottom',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,

                },
            }
        };

        var options2 = {
            height: '300',
            lineWidth: '3',
            pointSize: '10',
            chartArea: {left: '10%', width: '80%'},
            colors: ['#4ead33', '#f39200', '#ff4e32'],
            backgroundColor: 'transparent',
            hAxis: {
                baselineColor: '#f2f2f2',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,
                },
                gridlines: {
                    color: 'transparent'
                }
            },
            vAxis: {
                baselineColor: '#f2f2f2',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,
                },
                gridlines: {
                    color: 'transparent'
                },
                format: 'short',
                title: $("#declarations").data("chart-title"),
            },
            legend: {
                position: 'bottom',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,

                },
            },
        };

        var pieOptions = {
            colors: ['#92cb82', '#fc9281', '#f6f28f', '#f8be66', '#94c8de', '#8bd5be', '#bfb5d9', '#f9d0b3', '#a0a7b8',
                '#5b86b9', '#ee959f', '#fbb286', '#f1df8b'],
            chartArea: {left: 0, top: 0, width: '100%', height: '80%'},
            legend: {
                position: 'right',
                textStyle: {
                    color: '#000',
                    fontName: 'Montserrat',
                    fontSize: 12,

                },
            },
            pieSliceText: 'value',
            pieSliceTextStyle: {
                color: '#000',
                fontName: 'Montserrat',
                fontSize: 12,
            }
        };

        // declarationLineChart start
        if ($("#declarations-line-chart").length) {
            var dataDeclarationsLineChart = google.visualization.arrayToDataTable(
                $("#declarations").data("chart-data")
            );

            var declarationLineChart = new google.visualization.LineChart(document.getElementById('declarations-line-chart'));
            declarationLineChart.draw(dataDeclarationsLineChart, options2);
        }


        if ($("#cash-assets-line-chart").length) {
            var dataCashAssetsLineChart = google.visualization.arrayToDataTable(
                $("#cash-assets").data("chart-data")
            );
            var cashAssetsLineChart = new google.visualization.LineChart(document.getElementById('cash-assets-line-chart'));
            cashAssetsLineChart.draw(dataCashAssetsLineChart, options);
        }
    }
}
