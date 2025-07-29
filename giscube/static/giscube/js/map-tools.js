document.addEventListener('DOMContentLoaded', function() {
    function toggleFields() {
        const actionType = document.getElementById('id_action_type').value;
        const dependantFields = {
            'to': ['to'],
            'url': ['url', 'target'],
            'action': [],
            'webhook': ['url', 'headers', 'params']
        }
        const availableFields = document.querySelectorAll('.tab-action>.form-row')
        availableFields.forEach(function(field) {
            const fieldId = field.className.replaceAll('form-row', '').replaceAll('field-', '').trim();
            const isActionTypeField = fieldId === 'action_type';
            const isDependantField = dependantFields[actionType] && dependantFields[actionType].includes(fieldId);
            if (isActionTypeField || isDependantField) {
                field.style.display = '';
            } else {
                field.style.display = 'none';
            }
        });
    }
    var actionTypeField = document.getElementById('id_action_type');
    if (actionTypeField) {
        actionTypeField.addEventListener('change', toggleFields);
        toggleFields();
    }
});
