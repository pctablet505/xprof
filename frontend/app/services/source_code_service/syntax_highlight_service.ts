/**
 * @fileoverview Angular service wrapper for the 3P package highlightjs.
 *
 * OSS note: upstream this file imports `google3/third_party/javascript/
 * highlightjs/...` and relies on `hljs_<lang>` globals that only exist inside
 * Google's monorepo, so `ng build` fails in the public tree with six TS2304
 * errors. This is the only `google3/` import in the entire frontend, and it
 * alone blocks building the OSS frontend from source. Here it is expressed
 * against the public `highlight.js` package instead, which is the same library
 * the internal target wraps.
 */

import {Injectable} from '@angular/core';
import hljs from 'highlight.js/lib/core';
import bash from 'highlight.js/lib/languages/bash';
import c from 'highlight.js/lib/languages/c';
import cpp from 'highlight.js/lib/languages/cpp';
import css from 'highlight.js/lib/languages/css';
import go from 'highlight.js/lib/languages/go';
import java from 'highlight.js/lib/languages/java';
import javascript from 'highlight.js/lib/languages/javascript';
import kotlin from 'highlight.js/lib/languages/kotlin';
import python from 'highlight.js/lib/languages/python';
import sql from 'highlight.js/lib/languages/sql';
import typescript from 'highlight.js/lib/languages/typescript';
import xml from 'highlight.js/lib/languages/xml';

hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);
hljs.registerLanguage('go', go);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('c', c);
hljs.registerLanguage('cpp', cpp);
hljs.registerLanguage('kotlin', kotlin);
hljs.registerLanguage('css', css);
hljs.registerLanguage('bash', bash);
// highlight.js registers HTML under the `xml` grammar.
hljs.registerLanguage('html', xml);
hljs.registerLanguage('sql', sql);

/** A service for syntax highlighting. */
@Injectable({providedIn: 'root'})
export class SyntaxHighlightService {
  highlight(code: string, fileName?: string) {
    if (!fileName) {
      return hljs.highlightAuto(code);
    }
    const language = guessLanguage(fileName);
    if (!language) {
      return hljs.highlightAuto(code);
    }
    return hljs.highlight(code, {language});
  }
}

function guessLanguage(fileName: string): string|undefined {
  if (fileName.endsWith('.py')) {
    return 'python';
  } else if (fileName.endsWith('.java')) {
    return 'java';
  } else if (fileName.endsWith('.go')) {
    return 'go';
  } else if (fileName.endsWith('.ts')) {
    return 'typescript';
  } else if (fileName.endsWith('.js')) {
    return 'javascript';
  } else if (fileName.endsWith('.c')) {
    return 'c';
  } else if (fileName.endsWith('.cc') || fileName.endsWith('.cpp')) {
    return 'cpp';
  } else if (fileName.endsWith('.kt')) {
    return 'kotlin';
  } else if (fileName.endsWith('.css')) {
    return 'css';
  } else if (fileName.endsWith('.sh')) {
    return 'bash';
  } else if (fileName.endsWith('.html')) {
    return 'html';
  } else if (fileName.endsWith('.sql')) {
    return 'sql';
  }
  return undefined;
}
