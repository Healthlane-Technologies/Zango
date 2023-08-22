"use strict";

// Class definition
var KTProjectOverview = function () {
    // Colors
    var primary = KTUtil.getCssVariableValue('--bs-primary');
    var lightPrimary = KTUtil.getCssVariableValue('--bs-primary-light');
    var success = KTUtil.getCssVariableValue('--bs-success');
    var lightSuccess = KTUtil.getCssVariableValue('--bs-success-light');
    var gray200 = KTUtil.getCssVariableValue('--bs-gray-200');
    var gray500 = KTUtil.getCssVariableValue('--bs-gray-500');

    // Private functions
    var initChart = function () {        
        // init chart
        var element = document.getElementById("project_overview_chart");

        if (!element) {
            return;
        }

        var config = {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [30, 45, 25],
                    backgroundColor: ['#00A3FF', '#50CD89', '#E4E6EF']
                }],
                labels: ['Active', 'Completed', 'Yet to start']
            },
            options: {
                chart: {
                    fontFamily: 'inherit'
                },
                cutoutPercentage: 75,
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                title: {
                    display: false
                },
                animation: {
                    animateScale: true,
                    animateRotate: true
                },
                tooltips: {
                    enabled: true,
                    intersect: false,
                    mode: 'nearest',
                    bodySpacing: 5,
                    yPadding: 10,
                    xPadding: 10,
                    caretPadding: 0,
                    displayColors: false,
                    backgroundColor: '#20D489',
                    titleFontColor: '#ffffff',
                    cornerRadius: 4,
                    footerSpacing: 0,
                    titleSpacing: 0
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        };

        var ctx = element.getContext('2d');
        var myDoughnut = new Chart(ctx, config);
    }

    var initGraph = function () {
        var element = document.getElementById("kt_project_overview_graph");
        var height = parseInt(KTUtil.css(element, 'height'));

        if (!element) {
            return;
        }

        var options = {
            series: [{
                name: 'Incomplete',
                data: [70, 70, 80, 80, 75, 75, 75]
            }, {
                name: 'Complete',
                data: [55, 55, 60, 60, 55, 55, 60]
            }],
            chart: {
                type: 'area',
                height: height,
                toolbar: {
                    show: false
                }
            },
            plotOptions: {

            },
            legend: {
                show: false
            },
            dataLabels: {
                enabled: false
            },
            fill: {
                type: 'solid',
                opacity: 1
            },
            stroke: {
                curve: 'smooth',
                show: true,
                width: 3,
                colors: [primary, success]
            },
            xaxis: {
                categories: ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                axisBorder: {
                    show: false,
                },
                axisTicks: {
                    show: false
                },
                labels: {
                    style: {
                        colors: gray500,
                        fontSize: '12px'
                    }
                },
                crosshairs: {
                    position: 'front',
                    stroke: {
                        color: primary,
                        width: 1,
                        dashArray: 3
                    }
                },
                tooltip: {
                    enabled: true,
                    formatter: undefined,
                    offsetY: 0,
                    style: {
                        fontSize: '12px'
                    }
                }
            },
            yaxis: {
                labels: {
                    style: {
                        colors: gray500,
                        fontSize: '12px',
                    }
                }
            },
            states: {
                normal: {
                    filter: {
                        type: 'none',
                        value: 0
                    }
                },
                hover: {
                    filter: {
                        type: 'none',
                        value: 0
                    }
                },
                active: {
                    allowMultipleDataPointsSelection: false,
                    filter: {
                        type: 'none',
                        value: 0
                    }
                }
            },
            tooltip: {
                style: {
                    fontSize: '12px',
                },
                y: {
                    formatter: function (val) {
                        return val + " tasks"
                    }
                }
            },
            colors: [lightPrimary, lightSuccess],
            grid: {
                borderColor: gray200,
                strokeDashArray: 4,
                yaxis: {
                    lines: {
                        show: true
                    }
                }
            },
            markers: {
                //size: 5,
                colors: [lightPrimary, lightSuccess],
                strokeColor: [primary, success],
                strokeWidth: 3
            }
        };

        var chart = new ApexCharts(element, options);
        chart.render();
    }

    var initTable = function () {
        var table = document.querySelector('#kt_profile_overview_table');

        if (!table) {
            return;
        }

        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[1].innerHTML, "MMM D, YYYY").format();
            dateRow[1].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        const datatable = $(table).DataTable({
            "info": false,
            'order': []
        });

        // Filter dropdown elements
        const filterOrders = document.getElementById('kt_filter_orders');
        const filterYear = document.getElementById('kt_filter_year');

        // Filter by order status --- official docs reference: https://datatables.net/reference/api/search()
        filterOrders.addEventListener('change', function (e) {
            datatable.column(3).search(e.target.value).draw();
        });

        // Filter by date --- official docs reference: https://momentjs.com/docs/
        var minDate;
        var maxDate;

        filterYear.addEventListener('change', function (e) {
            const value = e.target.value;
            switch (value) {
                case 'thisyear': {
                    minDate = moment().startOf('year').format();
                    maxDate = moment().endOf('year').format();
                    datatable.draw();
                    break;
                }
                case 'thismonth': {
                    minDate = moment().startOf('month').format();
                    maxDate = moment().endOf('month').format();
                    datatable.draw();
                    break;
                }
                case 'lastmonth': {
                    minDate = moment().subtract(1, 'months').startOf('month').format();
                    maxDate = moment().subtract(1, 'months').endOf('month').format();
                    datatable.draw();
                    break;
                }
                case 'last90days': {
                    minDate = moment().subtract(30, 'days').format();
                    maxDate = moment().format();
                    datatable.draw();
                    break;
                }
                default: {
                    minDate = moment().subtract(100, 'years').startOf('month').format();
                    maxDate = moment().add(1, 'months').endOf('month').format();
                    datatable.draw();
                    break;
                }
            }
        });

        // Date range filter --- offical docs reference: https://datatables.net/examples/plug-ins/range_filtering.html
        $.fn.dataTable.ext.search.push(
            function (settings, data, dataIndex) {
                var min = minDate;
                var max = maxDate;
                var date = parseFloat(moment(data[1]).format()) || 0; // use data for the age column

                if ((isNaN(min) && isNaN(max)) ||
                    (isNaN(min) && date <= max) ||
                    (min <= date && isNaN(max)) ||
                    (min <= date && date <= max)) {
                    return true;
                }
                return false;
            }
        );

        // Search --- official docs reference: https://datatables.net/reference/api/search()
        var filterSearch = document.getElementById('kt_filter_search');
        filterSearch.addEventListener('keyup', function (e) {
            datatable.search(e.target.value).draw();
        });
    }

    // Public methods
    return {
        init: function () {
            initChart();
            initGraph();
            initTable();
        }
    }
}();


// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTProjectOverview.init();
});