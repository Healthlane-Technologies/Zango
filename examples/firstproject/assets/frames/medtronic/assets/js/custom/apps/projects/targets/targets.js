"use strict";

// Class definition
var KTProjectTargets = function () {

    var initDatatable = function () {
        const table = document.getElementById('kt_profile_overview_table');

        // set date data order
        const tableRows = table.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[1].innerHTML, "MMM D, YYYY").format();
            dateRow[1].setAttribute('data-order', realDate);
        });

        // init datatable --- more info on datatables: https://datatables.net/manual/
        const datatable = $(table).DataTable({
            "info": false,
            'order': [],
            "paging": false,
        });

    }

    // Public methods
    return {
        init: function () {
            initDatatable();
        }
    }
}();


// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTProjectTargets.init();
});
