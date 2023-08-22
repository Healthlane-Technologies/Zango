function initialize_regex(obj) {
  Object.keys(obj).forEach(function (key) {
    if (typeof obj[key] === 'object') {
      return initialize_regex(obj[key]);
    }
    if (key == 'regexp') {
      var re = new RegExp(obj[key]);
      obj[key] = re;
    }
  });
}

function initialize_validator(form_list) {
  var formv = {
    framework: 'uikit',
    icon: {
      valid: 'uk-icon-check',
      invalid: 'uk-icon-times',
      validating: 'uk-icon-refresh',
    },
    trigger: 'input change keyup',
  };
  for (var key in form_list) {
    $('input[type="file"]').each(function () {
      var clear_id = $(this).attr('name') + '-clear_id';
      if ($('#' + clear_id).length) {
        $('#' + clear_id).hide();
        $('[for=' + clear_id + ']').hide();
        delete form_list[key]['validation'][$(this).attr('name')];
      }
    });
    var form_id = form_list[key]['form_id'];
    var validation = form_list[key]['validation'];

    // add file validation from extra attribute
    Object.keys(validation).forEach(key => {
      if (key.includes('file')) {
        const dataExtSize = $(`#id_${key}`).attr('data-file-validation');
        if (dataExtSize) {
          const extraConfig = JSON.parse(
            JSON.stringify(eval('(' + dataExtSize + ')'))
          );
          validation[key]['validators'] = {
            ...validation[key]['validators'],
            file: extraConfig,
          };
        }
      }
    });

    initialize_regex(validation);
    formv['fields'] = validation;
    $(form_id).formValidation(formv);
  }
}
