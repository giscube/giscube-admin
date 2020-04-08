(function ($){
  var all_fields = ['name', 'description', 'title', 'path', 'url', 'file', 'layers', 'projection', 'getfeatureinfo_support', 'single_image'];

  function field_type_change() {
    var fields = {
      '': ['name', 'description', 'title'],
      'TMS': ['name', 'description', 'title', 'path', 'url', 'layers', 'projection'],
      'WMS': ['name', 'description', 'title', 'path', 'url', 'layers', 'projection', 'getfeatureinfo_support', 'single_image'],
      'document': ['name', 'description', 'title', 'file'],
      'url': ['name', 'description', 'title', 'url']
    };

    var item = $(this);
    var form = $(this).closest('form');
    var selected_fields = fields[item.val()];
    for (var i in all_fields){
      field = all_fields[i];
      if (selected_fields.indexOf(field) === -1){
        form.find('div.field-' + field).hide();
      }else{
        form.find('div.field-' + field).show();
      }
    }
  }

  function field_type_init(){
    field_type_change.call(this);
  }

  $(document).ready(function(){
    $('.field-type select').each(field_type_init);
    $('.field-type select').on('change', field_type_change);
  });

})(django.jQuery);
