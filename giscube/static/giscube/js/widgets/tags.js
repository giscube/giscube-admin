(function ($) {
  'use strict';
  const selector = 'textarea.tags-widget';
  const selectorSortable = 'tags.tags-widget';

  function init() {
    var $element = $(this);
    $element.hide();
    var $target = $('<input type="text" class="tags-widget">');
    $target.val($element.val());
    $($element).before($target);

    var tagify;
    function update_element () {
        var value = '', values = [];
        try {
          values = JSON.parse($target.val());
      } catch (err) {}
      for (var x in values){
          if (x > 0){
            value += ',';
          }
          value += values[x].value;
      }
      $element.val(value);
    }

    tagify = new Tagify($target[0], {callbacks: {
        add: update_element,
        remove: update_element
    }});
    $element.data('tagify', tagify);

    function onEnd(evt) {
      var item = tagify.value[evt.oldIndex];
      // Remove old index
      tagify.value.splice(evt.oldIndex, 1)
      var newIndex = evt.newIndex;
      if (evt.newIndex > evt.oldIndex){
          newIndex -= 1
      }
      // Insert item into new position
      tagify.value.splice(newIndex, 0, item);

      tagify.update();
      update_element();
    }

    Sortable.create($element.parent().find(selectorSortable)[0], {
      draggable: 'tag',
      onEnd: onEnd
    });
  };

  $(function () {
    $(selector).each(init);
  });

})(django.jQuery);
