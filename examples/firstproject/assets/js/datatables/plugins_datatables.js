$(function() {
    // datatables
    altair_datatables.dt_default();
    altair_datatables.dt_scroll();
    altair_datatables.dt_individual_search();
    altair_datatables.dt_colVis();
    altair_datatables.dt_tableExport();
});

altair_datatables = {
    dt_default: function() {
        var $dt_default = $('#dt_default');
        if($dt_default.length) {
            $dt_default.DataTable();
        }
    },
    dt_scroll: function() {
        var $dt_scroll = $('#dt_scroll');
        if($dt_scroll.length) {
            $dt_scroll.DataTable({
                "scrollY": "200px",
                "scrollCollapse": false,
                "paging": false
            });
        }
    },
    dt_individual_search: function() {
        var $dt_individual_search = $('#dt_individual_search');
        if($dt_individual_search.length) {

            // Setup - add a text input to each footer cell
            $dt_individual_search.find('tfoot th').each( function() {
                var title = $dt_individual_search.find('tfoot th').eq( $(this).index() ).text();
                $(this).html('<input type="text" class="md-input" placeholder="' + title + '" />');
            } );

            // reinitialize md inputs
            altair_md.inputs();

            // DataTable
            var individual_search_table = $dt_individual_search.DataTable();

            // Apply the search
            individual_search_table.columns().every(function() {
                var that = this;

                $('input', this.footer()).on('keyup change', function() {
                    that
                        .search( this.value )
                        .draw();
                } );
            });

        }
    },
    dt_colVis: function() {
        var $dt_colVis = $('#dt_colVis'),
            $dt_buttons = $dt_colVis.prev('.dt_colVis_buttons');

        if($dt_colVis.length) {

            // init datatables
            var colVis_table = $dt_colVis.DataTable({
                buttons: [
                    {
                        extend: 'colvis',
                        fade: 0
                    }
                ]
            });

            colVis_table.buttons().container().appendTo( $dt_buttons );

        }
    },
    dt_tableExport: function() {
        var $dt_tableExport = $('#dt_tableExport'),
            $dt_buttons = $dt_tableExport.prev('.dt_colVis_buttons');

        if($dt_tableExport.length) {
            var table_export = $dt_tableExport.DataTable({
                buttons: [
                    {
                        extend:    'copyHtml5',
                        text:      '<i class="uk-icon-files-o"></i> Copy',
                        titleAttr: 'Copy'
                    },
                    {
                        extend:    'print',
                        text:      '<i class="uk-icon-print"></i> Print',
                        titleAttr: 'Print'
                    },
                    {
                        extend:    'excelHtml5',
                        text:      '<i class="uk-icon-file-excel-o"></i> XLSX',
                        titleAttr: ''
                    },
                    {
                        extend:    'csvHtml5',
                        text:      '<i class="uk-icon-file-text-o"></i> CSV',
                        titleAttr: 'CSV'
                    },
                    {
                        extend:    'pdfHtml5',
                        text:      '<i class="uk-icon-file-pdf-o"></i> PDF',
                        titleAttr: 'PDF'
                    }
                ],
                processing: true,
                serverSide: true,
                language: {
                    search: "{{search_text}}"
                    },
                ajax: makeURL('/data-query/')
            });

            table_export.buttons().container().appendTo( $dt_buttons );

        }
    }
};