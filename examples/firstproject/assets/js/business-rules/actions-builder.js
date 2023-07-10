(function($) {
  $.fn.actionsBuilder = function(options) {
    if(options == "data") {
      var builder = $(this).eq(0).data("actionsBuilder");
      return builder.collectData();
    } else {
      return $(this).each(function() {
        var builder = new ActionsBuilder(this, options);
        $(this).data("actionsBuilder", builder);
      });
    }
  };

  function ActionsBuilder(element, options) {
    this.element = $(element);
    this.options = options || {};
    this.init();
  }

  ActionsBuilder.prototype = {
    init: function() {
      this.actions = this.options.actions;
      this.data = this.options.data || [];
      var actions = this.buildActions(this.data);
      this.element.html(actions);
    },

    buildActions: function(data) {
      var container = $("<div>", {"class": "actions"});
      var buttons = $("<div>", {"class": "action-buttons"});
      var addButton = $("<a>", {"href": "#", "class": "add", "text": "Add Action"});
      var _this = this;

      addButton.click(function(e) {
        e.preventDefault();
        container.append(_this.buildAction({}));
      });

      buttons.append(addButton);
      container.append(buttons);

      for(var i=0; i < data.length; i++) {
        var actionObj = data[i];
        var actionDiv = this.buildAction(actionObj);

        // Add values to params
        var params = [actionObj];
        var field;
        while(field = params.shift()) {
          actionDiv.find(":input[name='" + field.name + "']").val(field.value).change();
          if(field.params) params = params.concat(field.params);
        }
        container.append(actionDiv);
      }
      return container;
    },

    buildAction: function(data) {
      var field = this._findField(data.name);
      var div = $("<div>", {"class": "action"});
      var fieldsDiv = $("<div>", {"class": "subfields"});
      var select = $("<select>", {"class": "action-select", "name": "action-select"});

      for(var i=0; i < this.actions.length; i++) {
        var possibleField = this.actions[i];
        var option = $("<option>", {"text": possibleField.label, "value": possibleField.name});
        select.append(option);
      }

      var _this = this;
      select.change(function() {
        var val = $(this).val();
        var newField = _this._findField(val);
        fieldsDiv.empty();
        
        if(newField.params) {
          for (var key in newField.params) {
            fieldsDiv.append(_this.buildField(newField.params[key]));
          }
        }

        div.attr("class", "action " + val);
      });

      var removeLink = $("<a>", {"href": "#", "class": "remove", "text": "Remove Action"});
      removeLink.click(function(e) {
        e.preventDefault();
        div.remove();
      });

      if ( field ) {
        select.val(field.name);
        select.change();
        if ( data.params ) {
          for ( var key in data.params ) {
            fieldsDiv.find(':input[name=' + key + ']').val(data.params[key]);
          }
        }
      }
      else{
        select.change();
      }
      div.append(select);
      div.append(fieldsDiv);
      div.append(removeLink);
      return div;
    },

    buildField: function(field) {
      var div = $("<div>", {"class": "field"});
      var subfields = $("<div>", {"class": "subfields"});
      var _this = this;

      var label = $("<label>", {"text": field.label});
      div.append(label);

      if(field.fieldType == "select") {
        var label = $("<label>", {"text": field.label});
        var select = $("<select>", {"name": field.name});

        for(var i=0; i < field.options.length; i++) {
          var optionData = field.options[i];
          var option = $("<option>", {"text": optionData.label, "value": optionData.name});
          option.data("optionData", optionData);
          select.append(option);
        }

        select.change(function() {
          var option = $(this).find("> :selected");
          var optionData = option.data("optionData");
          subfields.empty();
          if(optionData.params) {
            for(var i=0; i < optionData.params.length; i++) {
              var f = optionData.params[i];
              subfields.append(_this.buildField(f));
            }
          }
        });

        select.change();
        div.append(select);
      } else if( field.fieldType == "text" ) {
        var input = $("<input>", {"type": "text", "name": field.name});
        div.append(input);
      } else if( field.fieldType == "numeric" ) {
        var input = $("<input>", {"type": "text", "name": field.name, "class": "numeric"});
        div.append(input);
      } else if( field.fieldType == "textarea" ) {
        var id = "textarea-" + Math.floor(Math.random() * 100000);
        var area = $("<textarea>", {"name": field.name, "id": id});
        div.append(area);
      }

      div.append(subfields);
      return div;
    },
                        

    collectData: function(params) {
      var _this = this;
      params = params || this.element.find(".action");
      var out = [];
      params.each(function() {
        var input = $(this).find("> :input");
        var subfields = $(this).find("> .subfields > .field");
        var value = input.val();
        if ( input.hasClass('numeric') ) {
          value = Number(value);
        }
        var action = {name: value};
        if(subfields.length > 0) {
          action.params = _this.collectParams(subfields);
        }
        out.push(action);
      });
      return out;
    },

    collectParams: function(params) {
      var out = {};
      params.each(function() {
        var input = $(this).find(':input');
        out[input.attr('name')] = input.val();
      });
      return out;
    },

    _findField: function(fieldName) {
      for(var i=0; i < this.actions.length; i++) {
        var field = this.actions[i];
        if(field.name == fieldName) return field;
      }
    }
  };

})(jQuery);
