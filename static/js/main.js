/*
 * jQuery File Upload Plugin JS Example 8.9.1
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */

/* global $, window */

$(function () {
    'use strict';

    // ★ 추가: 화면에 선택된 차단 확장자 목록 가져오기
    //  - 고정 확장자 체크박스 : <input type="checkbox" class="ext-fixed" value="bat">
    //  - 커스텀 확장자 태그  : <span class="ext-custom" data-ext="sh">sh</span>
    function getBlockedExtensions() {
        var blocked = [];

        // 1) 고정 확장자 체크박스
        $('.ext-fixed:checked').each(function () {
            blocked.push($(this).val().toLowerCase());
        });

        // 2) 커스텀 확장자 (태그 리스트 영역은 #custom-ext-list 라고 가정)
        $('#custom-ext-list .ext-custom').each(function () {
            blocked.push($(this).data('ext').toLowerCase());
        });

        return blocked;
    }

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        url: 'upload'
    });

    // ★ 추가: 업로드가 큐에 추가될 때 확장자 검사
    $('#fileupload').bind('fileuploadadd', function (e, data) {
        var blocked = getBlockedExtensions();
        if (!blocked.length) {
            // 차단 확장자가 하나도 없으면 바로 통과
            return;
        }

        var validFiles = [];
        $.each(data.files, function (index, file) {
            var name = file.name || '';
            var dotIndex = name.lastIndexOf('.');
            var ext = (dotIndex >= 0 ? name.substr(dotIndex + 1) : '').toLowerCase();

            if ($.inArray(ext, blocked) !== -1) {
                // 차단된 확장자
                alert('[' + name + '] 은(는) 차단된 확장자입니다.');
            } else {
                validFiles.push(file);
            }
        });

        // 차단되지 않은 파일만 남기기
        data.files = validFiles;

        // 하나도 안 남으면 업로드/큐 추가 자체를 취소
        if (!data.files.length) {
            return false;
        }
    });
    // ★ 추가 끝

    // Enable iframe cross-domain access via redirect option:
    $('#fileupload').fileupload(
        'option',
        'redirect',
        window.location.href.replace(
            /\/[^\/]*$/,
            '/cors/result.html?%s'
        )
    );

    if (window.location.hostname === 'blueimp.github.io') {
        // Demo settings:
        $('#fileupload').fileupload('option', {
            url: '//jquery-file-upload.appspot.com/',
            // Enable image resizing, except for Android and Opera,
            // which actually support image resizing, but fail to
            // send Blob objects via XHR requests:
            disableImageResize: /Android(?!.*Chrome)|Opera/
                .test(window.navigator.userAgent),
            maxFileSize: 5000000,
            acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i
        });
        // Upload server status check for browsers with CORS support:
        if ($.support.cors) {
            $.ajax({
                url: '//jquery-file-upload.appspot.com/',
                type: 'HEAD'
            }).fail(function () {
                $('<div class="alert alert-danger"/>')
                    .text('Upload server currently unavailable - ' +
                            new Date())
                    .appendTo('#fileupload');
            });
        }
    } else {
        // Load existing files:
        $('#fileupload').addClass('fileupload-processing');
        $.ajax({
            // Uncomment the following to send cross-domain cookies:
            //xhrFields: {withCredentials: true},
            url: $('#fileupload').fileupload('option', 'url'),
            dataType: 'json',
            context: $('#fileupload')[0]
        }).always(function () {
            $(this).removeClass('fileupload-processing');
        }).done(function (result) {
            $(this).fileupload('option', 'done')
                .call(this, $.Event('done'), {result: result});
        });
    }

});
