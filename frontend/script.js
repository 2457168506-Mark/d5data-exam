(function () {
  "use strict";

  var dropzone = document.getElementById("dropzone");
  var fileInput = document.getElementById("fileInput");
  var fileName = document.getElementById("fileName");
  var hint = dropzone.querySelector(".dropzone__hint");
  var lastStepBtn = document.getElementById("lastStepBtn");
  var dot3 = document.getElementById("dot3");

  // 第三步进度点：true 显示对勾（已完成），false 显示数字 3（进行中）。
  // 只用 class 切换，SVG 的 hidden 属性在部分内核不生效
  function setStep3(done) {
    dot3.classList.toggle("is-done", done);
    dot3.setAttribute(
      "aria-label",
      done ? "Step 3 completed" : "Step 3 in progress"
    );
  }

  // 点击 / 键盘触发文件选择框。
  // input 在 dropzone 内部，input.click() 派生的 click 事件会冒泡回来，
  // 必须忽略 target 为 input 的事件，否则会重复触发
  dropzone.addEventListener("click", function (event) {
    if (event.target === fileInput) return;
    fileInput.click();
  });

  dropzone.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      fileInput.click();
    }
  });

  // 选择文件后显示文件名
  fileInput.addEventListener("change", function () {
    showFileName(fileInput.files);
  });

  // 拖拽交互
  ["dragenter", "dragover"].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      dropzone.classList.add("is-dragover");
    });
  });

  ["dragleave", "drop"].forEach(function (type) {
    dropzone.addEventListener(type, function (event) {
      event.preventDefault();
      dropzone.classList.remove("is-dragover");
    });
  });

  dropzone.addEventListener("drop", function (event) {
    var files = event.dataTransfer && event.dataTransfer.files;
    if (files && files.length) {
      fileInput.files = files;
      showFileName(files);
    }
  });

  function showFileName(files) {
    if (!files || !files.length) return;
    fileName.textContent = files[0].name;
    fileName.hidden = false;
    hint.hidden = true;
    setStep3(true);
  }

  // Last step：清空已选文件，进度回到第三步进行中
  lastStepBtn.addEventListener("click", function () {
    fileInput.value = "";
    fileName.textContent = "";
    fileName.hidden = true;
    hint.hidden = false;
    setStep3(false);
  });
})();
