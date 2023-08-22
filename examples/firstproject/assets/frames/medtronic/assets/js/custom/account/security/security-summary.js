"use strict";

// Class definition
var KTAccountSecuritySummary = function () {
    // Private functions
    var initChart = function(tabSelector, chartSelector, data1, data2, initByDefault) {
        var element = document.querySelector(chartSelector);
        var height = parseInt(KTUtil.css(element, 'height'));

        if (!element) {
            return;
        }
 
        var options = {
            series: [{
                name: 'Net Profit',
                data: data1
            }, {
                name: 'Revenue',
                data: data2
            }],
            chart: {
                fontFamily: 'inherit',
                type: 'bar',
                height: height,
                toolbar: {
                    show: false
                }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: ['35%'],
                    borderRadius: 6
                }
            },
            legend: {
                show: false
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: {
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                axisBorder: {
                    show: false,
                },
                axisTicks: {
                    show: false
                },
                labels: {
                    style: {
                        colors: KTUtil.getCssVariableValue('--bs-gray-400'),
                        fontSize: '12px'
                    }
                }
            },
            yaxis: {
                labels: {
                    style: {
                        colors: KTUtil.getCssVariableValue('--bs-gray-400'),
                        fontSize: '12px'
                    }
                }
            },
            fill: {
                opacity: 1
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
                    fontSize: '12px'
                },
                y: {
                    formatter: function (val) {
                        return "$" + val + " thousands"
                    }
                }
            },
            colors: [KTUtil.getCssVariableValue('--bs-primary'), KTUtil.getCssVariableValue('--bs-gray-200')],
            grid: {
                borderColor: KTUtil.getCssVariableValue('--bs-gray-200'),
                strokeDashArray: 4,
                yaxis: {
                    lines: {
                        show: true
                    }
                }
            }
        };

        var chart = new ApexCharts(element, options);

        var init = false;
        var tab = document.querySelector(tabSelector);
        
        if (initByDefault === true) {
            setTimeout(function() {
                chart.render();
                init = true;
            }, 500);
        }        

        tab.addEventListener('shown.bs.tab', function (event) {
            if (init == false) {
                chart.render();
                init = true;
            }
        })
    } 

    // Public methods
    return {
        init: function () {
            initChart('#kt_security_summary_tab_hours_agents', '#kt_security_summary_chart_hours_agents', [50, 70, 90, 117, 80, 65, 80, 90, 115, 95, 70, 84], [50, 70, 90, 117, 80, 65, 70, 90, 115, 95, 70, 84], true);
            initChart('#kt_security_summary_tab_hours_clients', '#kt_security_summary_chart_hours_clients', [50, 70, 90, 117, 80, 65, 80, 90, 115, 95, 70, 84], [50, 70, 90, 117, 80, 65, 80, 90, 115, 95, 70, 84], false);
           
            initChart('#kt_security_summary_tab_day', '#kt_security_summary_chart_day_agents', [50, 70, 80, 100, 90, 65, 80, 90, 115, 95, 70, 84], [50, 70, 90, 117, 60, 65, 80, 90, 100, 95, 70, 84], false);
            initChart('#kt_security_summary_tab_day_clients', '#kt_security_summary_chart_day_clients', [50, 70, 100, 90, 80, 65, 80, 90, 115, 95, 70, 84], [50, 70, 90, 115, 80, 65, 80, 90, 115, 95, 70, 84], false);
           
            initChart('#kt_security_summary_tab_week', '#kt_security_summary_chart_week_agents', [50, 70, 75, 117, 80, 65, 80, 90, 115, 95, 50, 84], [50, 60, 90, 117, 80, 65, 80, 90, 115, 95, 70, 84], false);
            initChart('#kt_security_summary_tab_week_clients', '#kt_security_summary_chart_week_clients', [50, 70, 90, 117, 80, 65, 80, 90, 100, 80, 70, 84], [50, 70, 90, 117, 80, 65, 80, 90, 100, 95, 70, 84], false);
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTAccountSecuritySummary.init();
});
