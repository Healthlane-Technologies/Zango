(function($) {
  $.fn.conditionsBuilder = function(options) {
    if(options == "data") {
      var builder = $(this).eq(0).data("conditionsBuilder");
      return builder.collectData();
    } else {
      return $(this).each(function() {
        var builder = new ConditionsBuilder(this, options);
        $(this).data("conditionsBuilder", builder);
      });
    }
  };

  ConditionsBuilder = function(element, options) {
    this.element = $(element);
    this.options = options || {};
    this.init();
  }

  ConditionsBuilder.prototype = {
    init: function() {
      this.fields = this.denormalizeOperators(
              this.options.variables, this.options.variable_type_operators);
      this.data = this.options.data || {"all": []};
      var rules = this.buildRules(this.data);
      this.element.html(rules);
    },

    denormalizeOperators: function(variablesData, operators) {
      return $.map(variablesData, function(variable) {
          variable.operators = operators[variable.field_type];
          return variable;
      });
    },

    collectData: function() {
      return this.collectDataFromNode(this.element.find("> .conditional"));
    },

    collectDataFromNode: function(element) {
      var klass = null;
      var _this = this;
      if(element.is(".conditional")) {
        klass = element.find("> .all-any-wrapper > .all-any").val();
      }

      if(klass) {
        var out = {};
        out[klass] = [];
        element.find("> .conditional, > .rule").each(function() {
          out[klass].push(_this.collectDataFromNode($(this)));
        });
        return out;
      }
      else {
        var valueField = element.find(".value");
        var value = valueField.val();
        if (valueField.hasClass('numberInput')) {
            value = Number(value);
        }
        return {
          name: element.find(".field").val(),
          operator: element.find(".operator").val(),
          value: value
        };
      }
    },

    buildRules: function(ruleData) {
      return this.buildConditional(ruleData) || this.buildRule(ruleData);
    },

    buildConditional: function(ruleData) {
      var kind;
      if(ruleData.all) { kind = "all"; }
      else if(ruleData.any) { kind = "any"; }
      if(!kind) { return; }

      var div = $("<div>", {"class": "conditional " + kind});
      var selectWrapper = $("<div>", {"class": "all-any-wrapper"});
      var select = $("<select>", {"class": "all-any"});
      select.append($("<option>", {"value": "all", "text": "All", "selected": kind == "all"}));
      select.append($("<option>", {"value": "any", "text": "Any", "selected": kind == "any"}));
      selectWrapper.append(select);
      selectWrapper.append($("<h4>", {text: "of the following conditions:"}));
      div.append(selectWrapper);

      var addRuleLink = $("<a>", {"href": "#", "class": "add-rule", "text": "Add Condition"});
      var _this = this;
      addRuleLink.click(function(e) {
        e.preventDefault();
        var f = _this.fields[0];
        var newField = {name: f.value, operator: f.operators[0], value: null};
        div.append(_this.buildRule(newField));
      });
      div.append(addRuleLink);

      var addConditionLink = $("<a>", {"href": "#", "class": "add-condition", "text": "Add Sub-Condition"});
      addConditionLink.click(function(e) {
        e.preventDefault();
        var f = _this.fields[0];
        var newField = {"all": [{name: f.value, operator: f.operators[0], value: null}]};
        div.append(_this.buildConditional(newField));
      });
      div.append(addConditionLink);

      var removeLink = $("<a>", {"class": "remove", "href": "#", "text": "Remove This Sub-Condition"});
      removeLink.click(function(e) {
        e.preventDefault();
        div.remove();
      });
      div.append(removeLink);

      var rules = ruleData[kind];
      for(var i=0; i<rules.length; i++) {
        div.append(this.buildRules(rules[i]));
      }
      return div;
    },

    buildRule: function(ruleData) {
      var ruleDiv = $("<div>", {"class": "rule"});
      var fieldSelect = getFieldSelect(this.fields, ruleData);
      var operatorSelect = getOperatorSelect();

      fieldSelect.change(onFieldSelectChanged.call(this, operatorSelect, ruleData));

      ruleDiv.append(fieldSelect);
      ruleDiv.append(operatorSelect);
      ruleDiv.append(removeLink());

      fieldSelect.change();
      ruleDiv.find("> .value").val(ruleData.value);
      return ruleDiv;
    },

    operatorsFor: function(fieldName) {
      for(var i=0; i < this.fields.length; i++) {
        var field = this.fields[i];
        if(field.name == fieldName) {
          return field.operators;
        }
      }
    }
  };

  function getFieldSelect(fields, ruleData) {
    var select = $("<select>", {"class": "field"});
    for(var i=0; i < fields.length; i++) {
      var field = fields[i];
      var option = $("<option>", {
        text: field.label, 
        value: field.name, 
        selected: ruleData.name == field.name
      });
      option.data("options", field.options);
      select.append(option);
    }
    return select;
  }

  function getOperatorSelect() {
    var select = $("<select>", {"class": "operator"});
    select.change(onOperatorSelectChange);
    return select;
  }

  function removeLink() {
    var removeLink = $("<a>", {"class": "remove", "href": "#", "text": "Remove"});
    removeLink.click(onRemoveLinkClicked);
    return removeLink;
  }

  function onRemoveLinkClicked(e) {
    e.preventDefault();
    $(this).parents(".rule").remove();
  }

  function onFieldSelectChanged(operatorSelect, ruleData) {
    var builder = this;
    return function(e) {
      var operators = builder.operatorsFor($(e.target).val());
      operatorSelect.empty();
      for(var i=0; i < operators.length; i++) {
        var operator = operators[i];
        var option = $("<option>", {
          text: operator.label || operator.name, 
          value: operator.name, 
          selected: ruleData.operator == operator.name
        });
        option.data("field_type", operator.input_type);
        operatorSelect.append(option);
      }
      operatorSelect.change();
    }
  }

  function onOperatorSelectChange(e) {
    var $this = $(this);
    var option = $this.find("> :selected");
    var container = $this.parents(".rule");
    var fieldSelect = container.find(".field");
    var currentValue = container.find(".value");
    var val = currentValue.val();

    // Clear errorMessages when switching between operator types
    $this.nextAll().each( function(index) {
        if ( $(this).attr('class') == 'errorMessage' ) {
            $(this).remove();
        }});
    switch(option.data("field_type")) {
      case "none": 
        $this.after($("<input>", {"type": "hidden", "class": "value"}));
        break;
      case "text":
        $this.after($("<label class='errorMessage'></label>"));
        $this.after($("<input>", {"type": "text", "class": "value textInput"}));
        break;
      case "numeric":
        $this.after($("<label class='errorMessage'></label>"));
        $this.after($("<input>", {"type": "text", "class": "value numberInput"}));
        break;
      case "select":
        var select = $("<select>", {"class": "value"});
        var options = fieldSelect.find("> :selected").data("options");
        for(var i=0; i < options.length; i++) {
          var opt = options[i];
          select.append($("<option>", {"text": opt, "value": opt}));
        }
        $this.after(select);
        break;
      case "select_multiple":
        var options = fieldSelect.find("> :selected").data("options");
        var selectLength = options.length > 10 ? 10 : options.length;
        var select = $("<select class='value' multiple size='" + selectLength + "''></select>");
        for(var i=0; i <options.length; i++) {
          var opt = options[i];
          select.append($("<option>", {"text": opt, "value": opt}));
        }
        $this.after(select);
        break;
    }
    currentValue.remove();
  }

})($);
