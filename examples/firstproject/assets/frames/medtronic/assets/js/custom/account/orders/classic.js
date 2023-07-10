"use strict";

// Class definition
var KTDatatablesClassic = function () {
    // Private functions

    var initClassic = function () {

        // Set date data order
        const table = document.getElementById('kt_orders_classic');
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[1].innerHTML, "MMM D, YYYY").format('x');
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
                    minDate = moment().startOf('year').format('x');
                    maxDate = moment().endOf('year').format('x');
                    datatable.draw();
                    break;
                }
                case 'thismonth': {
                    minDate = moment().startOf('month').format('x');
                    maxDate = moment().endOf('month').format('x');
                    datatable.draw();
                    break;
                }
                case 'lastmonth': {
                    minDate = moment().subtract(1, 'months').startOf('month').format('x');
                    maxDate = moment().subtract(1, 'months').endOf('month').format('x');
                    datatable.draw();
                    break;
                }
                case 'last90days': {
                    minDate = moment().subtract(30, 'days').format('x');
                    maxDate = moment().format('x');
                    datatable.draw();
                    break;
                }
                default: {
                    minDate = moment().subtract(100, 'years').startOf('month').format('x');
                    maxDate = moment().add(1, 'months').endOf('month').format('x');
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
                var date = parseFloat(moment(data[1]).format('x')) || 0; // use data for the age column

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
            initClassic();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTDatatablesClassic.init();
});