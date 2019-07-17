(function ($) {
  'use strict';
  const selector = '.color-widget';

  function init () {
    var $element = $(this);
    $element.spectrum({
      allowEmpty: true,
      preferredFormat: 'hex'
    });
    $element.show();
  };

  $(function () {
    // Initialize all autocomplete widgets except the one in the template
    // form used when a new formset is added.
    $(selector).not('[name*=__prefix__]').each(init);
  });

  $(document).on('formset:added', function () {
    $(this).find(selector).each(init);
  });
})(django.jQuery);
