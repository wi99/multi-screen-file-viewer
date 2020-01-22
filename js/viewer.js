/**
 * @licstart The following is the entire license notice for the
 * Javascript code in this page
 *
 * Copyright 2019 Mozilla Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @licend The above is the entire license notice for the
 * Javascript code in this page
 */

/**
 * William's modifications: this is quite messy currently but I just took snippets from viewer.js, moved and dumbed down some code.
 */

function getViewerConfiguration() {
  return {
    appContainer: document.body,
    mainContainer: document.getElementById('viewerContainer'),
    viewerContainer: document.getElementById('viewer'),
    eventBus: null,
    toolbar: {
      container: document.getElementById('toolbarViewer'),
      numPages: document.getElementById('numPages'),
      pageNumber: document.getElementById('pageNumber'),
      scaleSelectContainer: document.getElementById('scaleSelectContainer'),
      scaleSelect: document.getElementById('scaleSelect'),
      customScaleOption: document.getElementById('customScaleOption'),
      previous: document.getElementById('previous'),
      next: document.getElementById('next'),
      zoomIn: document.getElementById('zoomIn'),
      zoomOut: document.getElementById('zoomOut'),
      viewFind: document.getElementById('viewFind'),
      openFile: document.getElementById('openFile'),
      print: document.getElementById('print'),
      presentationModeButton: document.getElementById('presentationMode'),
      download: document.getElementById('download'),
      viewBookmark: document.getElementById('viewBookmark')
    },
    secondaryToolbar: {
      toolbar: document.getElementById('secondaryToolbar'),
      toggleButton: document.getElementById('secondaryToolbarToggle'),
      toolbarButtonContainer: document.getElementById('secondaryToolbarButtonContainer'),
      presentationModeButton: document.getElementById('secondaryPresentationMode'),
      openFileButton: document.getElementById('secondaryOpenFile'),
      printButton: document.getElementById('secondaryPrint'),
      downloadButton: document.getElementById('secondaryDownload'),
      viewBookmarkButton: document.getElementById('secondaryViewBookmark'),
      firstPageButton: document.getElementById('firstPage'),
      lastPageButton: document.getElementById('lastPage'),
      pageRotateCwButton: document.getElementById('pageRotateCw'),
      pageRotateCcwButton: document.getElementById('pageRotateCcw'),
      cursorSelectToolButton: document.getElementById('cursorSelectTool'),
      cursorHandToolButton: document.getElementById('cursorHandTool'),
      scrollVerticalButton: document.getElementById('scrollVertical'),
      scrollHorizontalButton: document.getElementById('scrollHorizontal'),
      scrollWrappedButton: document.getElementById('scrollWrapped'),
      spreadNoneButton: document.getElementById('spreadNone'),
      spreadOddButton: document.getElementById('spreadOdd'),
      spreadEvenButton: document.getElementById('spreadEven'),
      documentPropertiesButton: document.getElementById('documentProperties')
    },
    fullscreen: {
      contextFirstPage: document.getElementById('contextFirstPage'),
      contextLastPage: document.getElementById('contextLastPage'),
      contextPageRotateCw: document.getElementById('contextPageRotateCw'),
      contextPageRotateCcw: document.getElementById('contextPageRotateCcw')
    },
    sidebar: {
      outerContainer: document.getElementById('outerContainer'),
      viewerContainer: document.getElementById('viewerContainer'),
      toggleButton: document.getElementById('sidebarToggle'),
      thumbnailButton: document.getElementById('viewThumbnail'),
      outlineButton: document.getElementById('viewOutline'),
      attachmentsButton: document.getElementById('viewAttachments'),
      thumbnailView: document.getElementById('thumbnailView'),
      outlineView: document.getElementById('outlineView'),
      attachmentsView: document.getElementById('attachmentsView')
    },
    sidebarResizer: {
      outerContainer: document.getElementById('outerContainer'),
      resizer: document.getElementById('sidebarResizer')
    },
    findBar: {
      bar: document.getElementById('findbar'),
      toggleButton: document.getElementById('viewFind'),
      findField: document.getElementById('findInput'),
      highlightAllCheckbox: document.getElementById('findHighlightAll'),
      caseSensitiveCheckbox: document.getElementById('findMatchCase'),
      entireWordCheckbox: document.getElementById('findEntireWord'),
      findMsg: document.getElementById('findMsg'),
      findResultsCount: document.getElementById('findResultsCount'),
      findPreviousButton: document.getElementById('findPrevious'),
      findNextButton: document.getElementById('findNext')
    },
    passwordOverlay: {
      overlayName: 'passwordOverlay',
      container: document.getElementById('passwordOverlay'),
      label: document.getElementById('passwordText'),
      input: document.getElementById('password'),
      submitButton: document.getElementById('passwordSubmit'),
      cancelButton: document.getElementById('passwordCancel')
    },
    documentProperties: {
      overlayName: 'documentPropertiesOverlay',
      container: document.getElementById('documentPropertiesOverlay'),
      closeButton: document.getElementById('documentPropertiesClose'),
      fields: {
        'fileName': document.getElementById('fileNameField'),
        'fileSize': document.getElementById('fileSizeField'),
        'title': document.getElementById('titleField'),
        'author': document.getElementById('authorField'),
        'subject': document.getElementById('subjectField'),
        'keywords': document.getElementById('keywordsField'),
        'creationDate': document.getElementById('creationDateField'),
        'modificationDate': document.getElementById('modificationDateField'),
        'creator': document.getElementById('creatorField'),
        'producer': document.getElementById('producerField'),
        'version': document.getElementById('versionField'),
        'pageCount': document.getElementById('pageCountField'),
        'pageSize': document.getElementById('pageSizeField'),
        'linearized': document.getElementById('linearizedField')
      }
    },
    errorWrapper: {
      container: document.getElementById('errorWrapper'),
      errorMessage: document.getElementById('errorMessage'),
      closeButton: document.getElementById('errorClose'),
      errorMoreInfo: document.getElementById('errorMoreInfo'),
      moreInfoButton: document.getElementById('errorShowMore'),
      lessInfoButton: document.getElementById('errorShowLess')
    },
    printContainer: document.getElementById('printContainer'),
    openFileInputName: 'fileInput',
    debuggerScriptPath: './debugger.js'
  };
}

var config = getViewerConfiguration();


var Toolbar = {
    _bindListeners: function _bindListeners() {
      var _this = this;

      var items = config.toolbar;
      var self = this;
      items.previous.addEventListener('click', function () {
        eventBus.dispatch('previouspage', {
          source: self
        });
      });
      items.next.addEventListener('click', function () {
        eventBus.dispatch('nextpage', {
          source: self
        });
      });
      items.zoomIn.addEventListener('click', function () {
        eventBus.dispatch('zoomin', {
          source: self
        });
      });
      items.zoomOut.addEventListener('click', function () {
        eventBus.dispatch('zoomout', {
          source: self
        });
      });
      items.pageNumber.addEventListener('click', function () {
        this.select();
      });
      items.pageNumber.addEventListener('change', function () {
        eventBus.dispatch('pagenumberchanged', {
          source: self,
          value: this.value
        });
      });
      items.scaleSelect.addEventListener('change', function () {
        if (this.value === 'custom') {
          return;
        }

        eventBus.dispatch('scalechanged', {
          source: self,
          value: this.value
        });
      });
      items.presentationModeButton.addEventListener('click', function () {
        eventBus.dispatch('presentationmode', {
          source: self
        });
      });
      items.openFile.addEventListener('click', function () {
        eventBus.dispatch('openfile', {
          source: self
        });
      });
      items.print.addEventListener('click', function () {
        eventBus.dispatch('print', {
          source: self
        });
      });
      items.download.addEventListener('click', function () {
        eventBus.dispatch('download', {
          source: self
        });
      });
    },
    _updateUIState: function _updateUIState() {
      var resetNumPages = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : false;

      if (!this._wasLocalized) {
        return;
      }

      var pageNumber = this.pageNumber,
          pagesCount = this.pagesCount,
          pageScaleValue = this.pageScaleValue,
          pageScale = this.pageScale,
          items = this.items;

      if (resetNumPages) {
        if (this.hasPageLabels) {
          items.pageNumber.type = 'text';
        } else {
          items.pageNumber.type = 'number';
          this.l10n.get('of_pages', {
            pagesCount: pagesCount
          }, 'of {{pagesCount}}').then(function (msg) {
            items.numPages.textContent = msg;
          });
        }

        items.pageNumber.max = pagesCount;
      }

      if (this.hasPageLabels) {
        items.pageNumber.value = this.pageLabel;
        this.l10n.get('page_of_pages', {
          pageNumber: pageNumber,
          pagesCount: pagesCount
        }, '({{pageNumber}} of {{pagesCount}})').then(function (msg) {
          items.numPages.textContent = msg;
        });
      } else {
        items.pageNumber.value = pageNumber;
      }

      items.previous.disabled = pageNumber <= 1;
      items.next.disabled = pageNumber >= pagesCount;
      items.zoomOut.disabled = pageScale <= _ui_utils.MIN_SCALE;
      items.zoomIn.disabled = pageScale >= _ui_utils.MAX_SCALE;
      var customScale = Math.round(pageScale * 10000) / 100;
      this.l10n.get('page_scale_percent', {
        scale: customScale
      }, '{{scale}}%').then(function (msg) {
        var options = items.scaleSelect.options;
        var predefinedValueFound = false;

        for (var i = 0, ii = options.length; i < ii; i++) {
          var option = options[i];

          if (option.value !== pageScaleValue) {
            option.selected = false;
            continue;
          }

          option.selected = true;
          predefinedValueFound = true;
        }

        if (!predefinedValueFound) {
          items.customScaleOption.textContent = msg;
          items.customScaleOption.selected = true;
        }
      });
    },
}


var eventBus = {
  _listeners: Object.create(null),
"on":
    function on(eventName, listener) {
      var eventListeners = this._listeners[eventName];

      if (!eventListeners) {
        eventListeners = [];
        this._listeners[eventName] = eventListeners;
      }

      eventListeners.push(listener);
    },
"dispatch":
    function dispatch(eventName, info) {
//      info['type'] = 'ctrl';
  //    info['action'] = eventName;
      // this aint video so it's fine to do the action on my end first and see if valid e.g. like the page thing idk though
      //// TODO: make action happen locally.      // actually maybe it's unneccesary i'll save it for later.
      ////

      if (info.source /* && info.source == Toolbar */) {
        info['type'] = 'ctrl';
        info['action'] = eventName;
        delete info['source'];
        websocket.send(JSON.stringify(info));
        return;
      }
      // else
      var eventListeners = this._listeners[eventName];

      if (!eventListeners || eventListeners.length === 0) {
        if (this._dispatchToDOM) {
          var _args5 = Array.prototype.slice.call(arguments, 1);

          this._dispatchDOMEvent(eventName, _args5);
        }

        return;
      }

      var args = Array.prototype.slice.call(arguments, 1);
      eventListeners.slice(0).forEach(function (listener) {
        listener.apply(null, args);
      });

      if (this._dispatchToDOM) {
        this._dispatchDOMEvent(eventName, args);
      }
    },
/*"_dispatchDOMEvent":
    function _dispatchDOMEvent(eventName) {
      var args = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var details = Object.create(null);

      if (args && args.length > 0) {
        var obj = args[0];

        for (var key in obj) {
          var value = obj[key];

          if (key === 'source') {
            if (value === window || value === document) {
              return;
            }

            continue;
          }

          details[key] = value;
        }
      }

      var event = document.createEvent('CustomEvent');
      event.initCustomEvent(eventName, true, true, details);
      document.dispatchEvent(event);
    },*/
}

Toolbar._bindListeners();



var DefaultExternalServices = {
  updateFindControlState: function updateFindControlState(data) {},
  updateFindMatchesCount: function updateFindMatchesCount(data) {},
  initPassiveLoading: function initPassiveLoading(callbacks) {},
  fallback: function fallback(data, callback) {},
  reportTelemetry: function reportTelemetry(data) {},
  createDownloadManager: function createDownloadManager(options) {
    throw new Error('Not implemented: createDownloadManager');
  },
  createPreferences: function createPreferences() {
    throw new Error('Not implemented: createPreferences');
  },
  createL10n: function createL10n(options) {
    throw new Error('Not implemented: createL10n');
  },
  supportsIntegratedFind: false,
  supportsDocumentFonts: true,
  supportsDocumentColors: true,
  supportedMouseWheelZoomModifierKeys: {
    ctrlKey: true,
    metaKey: true
  }
};

var PDFViewerApplication = {
  initialBookmark: document.location.hash.substring(1),
  initialized: false,
  fellback: false,
  appConfig: null,
  pdfDocument: null,
  pdfLoadingTask: null,
  printService: null,
  pdfViewer: null,
  pdfThumbnailViewer: null,
  pdfRenderingQueue: null,
  pdfPresentationMode: null,
  pdfDocumentProperties: null,
  pdfLinkService: null,
  pdfHistory: null,
  pdfSidebar: null,
  pdfSidebarResizer: null,
  pdfOutlineViewer: null,
  pdfAttachmentViewer: null,
  pdfCursorTools: null,
  store: null,
  downloadManager: null,
  overlayManager: null,
  preferences: null,
  toolbar: null,
  secondaryToolbar: null,
  eventBus: null,
  isInitialViewSet: false,
  downloadComplete: false,
  isViewerEmbedded: window.parent !== window,
  url: '',
  baseUrl: '',
  externalServices: DefaultExternalServices,
  _boundEvents: {},
  contentDispositionFilename: null,
  // stuff //

  bindEvents: function bindEvents() {
//    eventBus.on('resize', webViewerResize);
//    eventBus.on('hashchange', webViewerHashchange);
//    eventBus.on('beforeprint', _boundEvents.beforePrint);
//    eventBus.on('afterprint', _boundEvents.afterPrint);
//    eventBus.on('pagerendered', webViewerPageRendered);
//    eventBus.on('textlayerrendered', webViewerTextLayerRendered);
//    eventBus.on('updateviewarea', webViewerUpdateViewarea);
//    eventBus.on('pagechanging', webViewerPageChanging);
//    eventBus.on('scalechanging', webViewerScaleChanging);
//    eventBus.on('rotationchanging', webViewerRotationChanging);
//    eventBus.on('sidebarviewchanged', webViewerSidebarViewChanged);
//    eventBus.on('pagemode', webViewerPageMode);
//    eventBus.on('namedaction', webViewerNamedAction);
//    eventBus.on('presentationmodechanged', webViewerPresentationModeChanged);
//    eventBus.on('presentationmode', webViewerPresentationMode);
//    eventBus.on('openfile', webViewerOpenFile);
//    eventBus.on('print', webViewerPrint); // TODO
//    eventBus.on('download', webViewerDownload); // TODO
//    eventBus.on('firstpage', webViewerFirstPage); // TODO (in the 2ndary toolbar)
//    eventBus.on('lastpage', webViewerLastPage); // TODO (in the 2ndary toolbar)
    eventBus.on('nextpage', webViewerNextPage);
    eventBus.on('previouspage', webViewerPreviousPage);
//    eventBus.on('zoomin', webViewerZoomIn); // TODO
//    eventBus.on('zoomout', webViewerZoomOut); // TODO
//    eventBus.on('zoomreset', webViewerZoomReset); // TODO
    eventBus.on('pagenumberchanged', webViewerPageNumberChanged);
//    eventBus.on('scalechanged', webViewerScaleChanged); // TODO
//    eventBus.on('rotatecw', webViewerRotateCw); // TODO
//    eventBus.on('rotateccw', webViewerRotateCcw); // TODO
//    eventBus.on('switchscrollmode', webViewerSwitchScrollMode);
//    eventBus.on('scrollmodechanged', webViewerScrollModeChanged);
//    eventBus.on('switchspreadmode', webViewerSwitchSpreadMode);
//    eventBus.on('spreadmodechanged', webViewerSpreadModeChanged);
//    eventBus.on('documentproperties', webViewerDocumentProperties);
//    eventBus.on('find', webViewerFind);
//    eventBus.on('findfromurlhash', webViewerFindFromUrlHash);
//    eventBus.on('updatefindmatchescount', webViewerUpdateFindMatchesCount);
//    eventBus.on('updatefindcontrolstate', webViewerUpdateFindControlState);
//    eventBus.on('fileinputchange', webViewerFileInputChange);
  },
  
  rendering: false,
  // now i see why viewer.js made them invisible.
 // page: 2, // This is the cause of the bad stuff.
 // numPages: 1,
  

}

exports = {};
var CSS_UNITS = 96.0 / 72.0;
exports.CSS_UNITS = CSS_UNITS;
var DEFAULT_SCALE_VALUE = 'auto';
exports.DEFAULT_SCALE_VALUE = DEFAULT_SCALE_VALUE;
var DEFAULT_SCALE = 1.0;
exports.DEFAULT_SCALE = DEFAULT_SCALE;
var MIN_SCALE = 0.10;
exports.MIN_SCALE = MIN_SCALE;
var MAX_SCALE = 10.0;
exports.MAX_SCALE = MAX_SCALE;
var UNKNOWN_SCALE = 0;
exports.UNKNOWN_SCALE = UNKNOWN_SCALE;
var MAX_AUTO_SCALE = 1.25;
exports.MAX_AUTO_SCALE = MAX_AUTO_SCALE;
var SCROLLBAR_PADDING = 40;
exports.SCROLLBAR_PADDING = SCROLLBAR_PADDING;
var VERTICAL_PADDING = 5;
exports.VERTICAL_PADDING = VERTICAL_PADDING;
_ui_utils = exports;







function clamp(v, min, max) {
  return Math.min(Math.max(v, min), max);
}



/*
function webViewerPrint() {
  window.print();
}

function webViewerDownload() {
  PDFViewerApplication.download();
}

function webViewerFirstPage() {
  if (PDFViewerApplication.pdfDocument) {
    PDFViewerApplication.page = 1;
  }
}

function webViewerLastPage() {
  if (PDFViewerApplication.pdfDocument) {
    PDFViewerApplication.page = PDFViewerApplication.pagesCount;
  }
}
*/
function webViewerNextPage() {
  changePage(PDFViewerApplication.page+1);
}

function webViewerPreviousPage() {
  changePage(PDFViewerApplication.page-1); // TODO: ditch nextpage and prevpage and only do absolute. also don't restart on refresh.
}
/*
function webViewerZoomIn() {
  PDFViewerApplication.zoomIn();
}

function webViewerZoomOut() {
  PDFViewerApplication.zoomOut();
}

function webViewerZoomReset() {
  PDFViewerApplication.zoomReset();
}
*/

function webViewerPageNumberChanged(evt) {
  changePage(Number(evt.value));
}

function changePage(num){
  PDFViewerApplication.page = num;
  if (PDFViewerApplication.page <= 0) {
    PDFViewerApplication.page = 1;
    return;
  }
  if (PDFViewerApplication.page > PDFViewerApplication.numPages) {
    PDFViewerApplication.page = PDFViewerApplication.numPages;
    return;
  }
  if (!rendering) loadingTask.promise.then(renderPages);
  config.toolbar.pageNumber.value = String(PDFViewerApplication.page)
}

/*
function webViewerScaleChanged(evt) {
  PDFViewerApplication.pdfViewer.currentScaleValue = evt.value;
}
*/



//////////

PDFViewerApplication.bindEvents();
