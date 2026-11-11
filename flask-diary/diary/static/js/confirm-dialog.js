// Подтверждение действия в окне <dialog> для форм с атрибутом data-confirm-dialog="<id окна>".
// Внешний файл без встроенного кода: так работает строгая политика безопасности (CSP).
(function () {
  'use strict';

  document.querySelectorAll('form[data-confirm-dialog]').forEach(function (form) {
    var dialog = document.getElementById(form.dataset.confirmDialog);
    // В браузерах без поддержки <dialog> форма отправляется сразу, как без скрипта.
    if (!dialog || typeof dialog.showModal !== 'function') {
      return;
    }

    var confirmed = false;

    form.addEventListener('submit', function (event) {
      if (confirmed) {
        return;
      }
      event.preventDefault();
      dialog.returnValue = '';
      dialog.showModal();
    });

    dialog.addEventListener('close', function () {
      if (dialog.returnValue === 'confirm') {
        confirmed = true;
        form.requestSubmit();
      }
    });
  });
})();
