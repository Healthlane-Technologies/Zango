"use strict";

// Class definition
var KTProjectUsers = function () {

    var initTable = function () {
        // Set date data order
        const table = document.getElementById('kt_project_users_table');

        if (!table) {
            return;
        }
        
        const tableRows = table.querySelectorAll('tbody tr');
        
        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const realDate = moment(dateRow[1].innerHTML, "MMM D, YYYY").format();
            dateRow[1].setAttribute('data-order', realDate);
        });

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        const datatable = $(table).DataTable({
            "info": false,
            'order': [],
            "columnDefs": [{
                "targets": 4,
                "orderable": false
            }]
        });

        // Search --- official docs reference: https://datatables.net/reference/api/search()
        var filterSearch = document.getElementById('kt_filter_search');
        if (filterSearch) {
            filterSearch.addEventListener('keyup', function (e) {
                datatable.search(e.target.value).draw();
            });
        }        
    }

    // Public methods
    return {
        init: function () {
            initTable();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function() {
    KTProjectUsers.init();
});