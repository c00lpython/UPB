import { NodeConnectionTypes } from 'n8n-workflow';
import type { INodeType, INodeTypeDescription } from 'n8n-workflow';

export class UPBParser implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'UPB Parser',
    name: 'upbParser',
    icon: 'file:upb-icon.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"]}}',
    description: 'Universal Parser Builder - Web scraping and automation with all block types',
    defaults: { name: 'UPB Parser' },
    usableAsTool: true,
    inputs: [NodeConnectionTypes.Main],
    outputs: [NodeConnectionTypes.Main],
    properties: [
      // ==================== ОПЕРАЦИИ (ВСЕ 26) ====================
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        options: [
          // Навигация
          { name: '🌐 1. Open URL', value: 'openUrl' },
          { name: '⬅️ 2. Go Back', value: 'goBack' },
          { name: '🔄 3. Refresh', value: 'refresh' },
          // Взаимодействие
          { name: '🖱️ 4. Click', value: 'click' },
          { name: '⌨️ 5. Type Text', value: 'type' },
          { name: '👆 6. Hover', value: 'hover' },
          { name: '📜 7. Scroll To', value: 'scrollTo' },
          { name: '📋 8. Select Dropdown', value: 'selectDropdown' },
          // Ожидание
          { name: '⏳ 9. Wait (seconds)', value: 'wait' },
          { name: '⏰ 10. Wait For Element', value: 'waitForElement' },
          { name: '🚦 11. Wait For Navigation', value: 'waitForNavigation' },
          // Извлечение данных
          { name: '📝 12. Extract Text', value: 'extractText' },
          { name: '🏷️ 13. Extract Attribute', value: 'extractAttribute' },
          { name: '📄 14. Extract HTML', value: 'extractHtml' },
          { name: '📋 15. Extract List', value: 'extractList' },
          // Переменные
          { name: '➕ 16. Create Variable', value: 'createVariable' },
          { name: '✏️ 17. Update Variable', value: 'updateVariable' },
          { name: '📚 18. Create List', value: 'createList' },
          { name: '📌 19. Append To List', value: 'appendToList' },
          { name: '🗑️ 20. Clear List', value: 'clearList' },
          // Вывод
          { name: '📊 21. Save to Excel', value: 'saveExcel' },
          { name: '💾 22. Save to JSON', value: 'saveJson' },
          { name: '🤖 23. Send Telegram', value: 'sendTelegram' },
          { name: '📸 24. Screenshot', value: 'screenshot' },
          // Отладка
          { name: '🖨️ 25. Print to Console', value: 'print' },
          { name: '📝 26. Write Log', value: 'log' },
        ],
        default: 'extractText',
      },

      // ==================== ОБЩИЕ ПАРАМЕТРЫ ====================
      {
        displayName: 'URL',
        name: 'url',
        type: 'string',
        default: '',
        required: true,
        displayOptions: {
          show: { operation: ['openUrl', 'extractText', 'extractAttribute', 'extractHtml', 'extractList'] },
        },
      },
      {
        displayName: 'Save To Variable',
        name: 'saveTo',
        type: 'string',
        default: 'result',
        displayOptions: {
          show: { operation: ['extractText', 'extractAttribute', 'extractHtml', 'extractList'] },
        },
      },

      // ==================== СЕЛЕКТОР ====================
      {
        displayName: 'Selector Type',
        name: 'selectorType',
        type: 'options',
        options: [
          { name: 'CSS Selector', value: 'css' },
          { name: 'XPath', value: 'xpath' },
        ],
        default: 'css',
        displayOptions: {
          show: { operation: ['click', 'type', 'hover', 'scrollTo', 'selectDropdown', 'extractText', 'extractAttribute', 'extractHtml', 'extractList', 'waitForElement'] },
        },
      },
      {
        displayName: 'Selector',
        name: 'selector',
        type: 'string',
        default: '',
        required: true,
        displayOptions: {
          show: { operation: ['click', 'type', 'hover', 'scrollTo', 'selectDropdown', 'extractText', 'extractAttribute', 'extractHtml', 'extractList', 'waitForElement'] },
        },
      },

      // ==================== ТИП ====================
      {
        displayName: 'Text',
        name: 'text',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['type'] } },
      },
      {
        displayName: 'Clear First',
        name: 'clearFirst',
        type: 'boolean',
        default: true,
        displayOptions: { show: { operation: ['type'] } },
      },
      {
        displayName: 'Press Enter',
        name: 'pressEnter',
        type: 'boolean',
        default: false,
        displayOptions: { show: { operation: ['type'] } },
      },
      {
        displayName: 'Wait For Navigation',
        name: 'waitForNavigation',
        type: 'boolean',
        default: false,
        displayOptions: { show: { operation: ['click'] } },
      },

      // ==================== ВЫБОР ИЗ СПИСКА ====================
      {
        displayName: 'Value',
        name: 'value',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['selectDropdown'] } },
      },

      // ==================== ОЖИДАНИЕ ====================
      {
        displayName: 'Seconds',
        name: 'seconds',
        type: 'number',
        default: 1,
        typeOptions: { minValue: 0.1, numberPrecision: 1 },
        displayOptions: { show: { operation: ['wait'] } },
      },
      {
        displayName: 'Timeout (ms)',
        name: 'timeout',
        type: 'number',
        default: 5000,
        displayOptions: { show: { operation: ['waitForElement', 'waitForNavigation'] } },
      },
      {
        displayName: 'State',
        name: 'state',
        type: 'options',
        options: [
          { name: 'Visible', value: 'visible' },
          { name: 'Hidden', value: 'hidden' },
        ],
        default: 'visible',
        displayOptions: { show: { operation: ['waitForElement'] } },
      },

      // ==================== ИЗВЛЕЧЕНИЕ ====================
      {
        displayName: 'Attribute Name',
        name: 'attributeName',
        type: 'string',
        default: '',
        placeholder: 'href, src, alt, class...',
        displayOptions: { show: { operation: ['extractAttribute'] } },
      },
      {
        displayName: 'Trim',
        name: 'trim',
        type: 'boolean',
        default: true,
        displayOptions: { show: { operation: ['extractText'] } },
      },
      {
        displayName: 'Container Selector',
        name: 'containerSelector',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['extractList'] } },
      },
      {
        displayName: 'Fields',
        name: 'fields',
        type: 'fixedCollection',
        typeOptions: { multipleValues: true },
        default: {},
        displayOptions: { show: { operation: ['extractList'] } },
        options: [{
          name: 'field',
          displayName: 'Field',
          values: [
            { displayName: 'Field Name', name: 'fieldName', type: 'string', default: '' },
            { displayName: 'Selector', name: 'fieldSelector', type: 'string', default: '' },
            {
              displayName: 'Extract Type', name: 'extractType', type: 'options',
              options: [{ name: 'Text', value: 'text' }, { name: 'HTML', value: 'html' }, { name: 'Attribute', value: 'attribute' }],
              default: 'text',
            },
            { displayName: 'Attribute Name', name: 'attributeName', type: 'string', default: '', displayOptions: { show: { extractType: ['attribute'] } } },
          ],
        }],
      },

      // ==================== ПЕРЕМЕННЫЕ ====================
      {
        displayName: 'Variable Name',
        name: 'varName',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['createVariable', 'updateVariable', 'createList', 'clearList'] } },
      },
      {
        displayName: 'Initial Value',
        name: 'initialValue',
        type: 'string',
        default: '',
        displayOptions: { show: { operation: ['createVariable'] } },
      },
      {
        displayName: 'Value',
        name: 'varValue',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['updateVariable', 'appendToList'] } },
      },
      {
        displayName: 'List Name',
        name: 'listName',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['appendToList'] } },
      },

      // ==================== ВЫВОД ====================
      {
        displayName: 'Data (variable name)',
        name: 'data',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['saveExcel', 'saveJson'] } },
      },
      {
        displayName: 'Filename',
        name: 'filename',
        type: 'string',
        default: 'output.xlsx',
        displayOptions: { show: { operation: ['saveExcel', 'saveJson', 'screenshot'] } },
      },
      {
        displayName: 'Sheet Name',
        name: 'sheetName',
        type: 'string',
        default: 'Sheet1',
        displayOptions: { show: { operation: ['saveExcel'] } },
      },
      {
        displayName: 'Bot Token',
        name: 'botToken',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['sendTelegram'] } },
      },
      {
        displayName: 'Chat ID',
        name: 'chatId',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['sendTelegram'] } },
      },
      {
        displayName: 'Message',
        name: 'message',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['sendTelegram', 'log'] } },
      },
      {
        displayName: 'Full Page',
        name: 'fullPage',
        type: 'boolean',
        default: false,
        displayOptions: { show: { operation: ['screenshot'] } },
      },

      // ==================== ОТЛАДКА ====================
      {
        displayName: 'Value to Print',
        name: 'printValue',
        type: 'string',
        default: '',
        required: true,
        displayOptions: { show: { operation: ['print'] } },
      },
      {
        displayName: 'Log Level',
        name: 'logLevel',
        type: 'options',
        options: [
          { name: 'Info', value: 'info' },
          { name: 'Warning', value: 'warning' },
          { name: 'Error', value: 'error' },
        ],
        default: 'info',
        displayOptions: { show: { operation: ['log'] } },
      },
    ],
  };

  async execute(this: any): Promise<any> {
    const operation = this.getNodeParameter('operation', 0);
    const variables: Record<string, any> = this.getWorkflowStaticData('global') || {};
    
    // Инициализация браузера для DOM-операций
    let browser: any = null;
    let page: any = null;
    let context: any = null;
    
    const domOperations = ['openUrl', 'goBack', 'refresh', 'click', 'type', 'hover', 'scrollTo', 'selectDropdown', 'waitForElement', 'waitForNavigation', 'extractText', 'extractAttribute', 'extractHtml', 'extractList', 'screenshot'];
    
    try {
      if (domOperations.includes(operation)) {
        const { chromium } = require('playwright');
        browser = await chromium.launch({ headless: true });
        context = await browser.newContext();
        page = await context.newPage();
      }
      
      let result: any = null;
      
      switch (operation) {
        case 'openUrl': {
          const url = this.getNodeParameter('url', 0);
          const waitUntil = this.getNodeParameter('waitUntil', 0) || 'load';
          await page.goto(url, { waitUntil });
          result = { url, loaded: true };
          break;
        }
        
        case 'goBack': {
          await page.goBack();
          result = { url: page.url() };
          break;
        }
        
        case 'refresh': {
          await page.reload();
          result = { url: page.url() };
          break;
        }
        
        case 'click': {
          const selectorType = this.getNodeParameter('selectorType', 0);
          const selector = this.getNodeParameter('selector', 0);
          const waitForNav = this.getNodeParameter('waitForNavigation', 0);
          
          if (waitForNav) {
            await Promise.all([page.waitForNavigation(), selectorType === 'xpath' ? page.locator(`xpath=${selector}`).click() : page.click(selector)]);
          } else {
            if (selectorType === 'xpath') {
              await page.locator(`xpath=${selector}`).click();
            } else {
              await page.click(selector);
            }
          }
          result = { clicked: selector };
          break;
        }
        
        case 'type': {
          const selectorType = this.getNodeParameter('selectorType', 0);
          const selector = this.getNodeParameter('selector', 0);
          const text = this.getNodeParameter('text', 0);
          const clearFirst = this.getNodeParameter('clearFirst', 0);
          const pressEnter = this.getNodeParameter('pressEnter', 0);
          
          if (selectorType === 'xpath') {
            const locator = page.locator(`xpath=${selector}`);
            if (clearFirst) await locator.fill('');
            await locator.type(text);
            if (pressEnter) await locator.press('Enter');
          } else {
            if (clearFirst) await page.fill(selector, '');
            await page.type(selector, text);
            if (pressEnter) await page.keyboard.press('Enter');
          }
          result = { typed: text };
          break;
        }
        
        case 'hover': {
          const selectorType = this.getNodeParameter('selectorType', 0);
          const selector = this.getNodeParameter('selector', 0);
          if (selectorType === 'xpath') {
            await page.locator(`xpath=${selector}`).hover();
          } else {
            await page.hover(selector);
          }
          result = { hovered: selector };
          break;
        }
        
        case 'scrollTo': {
          const selector = this.getNodeParameter('selector', 0);
          await page.locator(selector).scrollIntoViewIfNeeded();
          result = { scrolledTo: selector };
          break;
        }
        
        case 'selectDropdown': {
          const selector = this.getNodeParameter('selector', 0);
          const value = this.getNodeParameter('value', 0);
          await page.selectOption(selector, value);
          result = { selected: value };
          break;
        }
        
        case 'wait': {
          const seconds = this.getNodeParameter('seconds', 0);
          await new Promise(resolve => setTimeout(resolve, seconds * 1000));
          result = { waited: seconds };
          break;
        }
        
        case 'waitForElement': {
          const selector = this.getNodeParameter('selector', 0);
          const timeout = this.getNodeParameter('timeout', 0);
          const state = this.getNodeParameter('state', 0);
          await page.waitForSelector(selector, { timeout, state });
          result = { elementFound: selector };
          break;
        }
        
        case 'waitForNavigation': {
          const timeout = this.getNodeParameter('timeout', 0);
          await page.waitForNavigation({ timeout });
          result = { url: page.url() };
          break;
        }
        
        case 'extractText': {
          const selector = this.getNodeParameter('selector', 0);
          const trim = this.getNodeParameter('trim', 0);
          let text = await page.textContent(selector);
          if (trim && text) text = text.trim();
          result = text;
          break;
        }
        
        case 'extractAttribute': {
          const selector = this.getNodeParameter('selector', 0);
          const attributeName = this.getNodeParameter('attributeName', 0);
          result = await page.getAttribute(selector, attributeName);
          break;
        }
        
        case 'extractHtml': {
          const selector = this.getNodeParameter('selector', 0);
          result = await page.innerHTML(selector);
          break;
        }
        
        case 'extractList': {
          const containerSelector = this.getNodeParameter('containerSelector', 0);
          const fields = this.getNodeParameter('fields', 0) || {};
          const items: any[] = [];
          const elements = await page.$$(containerSelector);
          
          for (const el of elements) {
            const item: any = {};
            if (fields.field && Array.isArray(fields.field)) {
              for (const field of fields.field) {
                const fieldName = field.fieldName;
                const fieldSelector = field.fieldSelector;
                const extractType = field.extractType || 'text';
                
                if (extractType === 'text') {
                  const text = await el.textContent(fieldSelector);
                  item[fieldName] = text?.trim() || '';
                } else if (extractType === 'html') {
                  const html = await el.innerHTML(fieldSelector);
                  item[fieldName] = html || '';
                } else if (extractType === 'attribute') {
                  const attrName = field.attributeName;
                  const attr = await el.getAttribute(fieldSelector, attrName);
                  item[fieldName] = attr || '';
                }
              }
            }
            items.push(item);
          }
          result = items;
          break;
        }
        
        case 'createVariable': {
          const varName = this.getNodeParameter('varName', 0);
          const initialValue = this.getNodeParameter('initialValue', 0);
          variables[varName] = this.resolveValue(initialValue, variables);
          result = { [varName]: variables[varName] };
          break;
        }
        
        case 'updateVariable': {
          const varName = this.getNodeParameter('varName', 0);
          const varValue = this.getNodeParameter('varValue', 0);
          variables[varName] = this.resolveValue(varValue, variables);
          result = { [varName]: variables[varName] };
          break;
        }
        
        case 'createList': {
          const varName = this.getNodeParameter('varName', 0);
          variables[varName] = [];
          result = { [varName]: [] };
          break;
        }
        
        case 'appendToList': {
          const listName = this.getNodeParameter('listName', 0);
          const varValue = this.getNodeParameter('varValue', 0);
          if (!variables[listName]) variables[listName] = [];
          variables[listName].push(this.resolveValue(varValue, variables));
          result = { [listName]: variables[listName] };
          break;
        }
        
        case 'clearList': {
          const varName = this.getNodeParameter('varName', 0);
          variables[varName] = [];
          result = { [varName]: [] };
          break;
        }
        
        case 'saveExcel': {
          const dataVar = this.getNodeParameter('data', 0);
          const filename = this.getNodeParameter('filename', 0);
          const sheetName = this.getNodeParameter('sheetName', 0);
          const data = this.resolveValue(dataVar, variables);
          const XLSX = require('xlsx');
          const ws = XLSX.utils.json_to_sheet(Array.isArray(data) ? data : [data]);
          const wb = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(wb, ws, sheetName);
          XLSX.writeFile(wb, filename);
          result = { saved: filename, rows: Array.isArray(data) ? data.length : 1 };
          break;
        }
        
        case 'saveJson': {
          const dataVar = this.getNodeParameter('data', 0);
          const filename = this.getNodeParameter('filename', 0);
          const data = this.resolveValue(dataVar, variables);
          const fs = require('fs');
          fs.writeFileSync(filename, JSON.stringify(data, null, 2));
          result = { saved: filename };
          break;
        }
        
        case 'sendTelegram': {
          const botToken = this.getNodeParameter('botToken', 0);
          const chatId = this.getNodeParameter('chatId', 0);
          const message = this.resolveValue(this.getNodeParameter('message', 0), variables);
          const axios = require('axios');
          await axios.post(`https://api.telegram.org/bot${botToken}/sendMessage`, { chat_id: chatId, text: message });
          result = { sent: true };
          break;
        }
        
        case 'screenshot': {
          const filename = this.getNodeParameter('filename', 0);
          const fullPage = this.getNodeParameter('fullPage', 0);
          await page.screenshot({ path: filename, fullPage });
          result = { screenshot: filename };
          break;
        }
        
        case 'print': {
          const value = this.resolveValue(this.getNodeParameter('printValue', 0), variables);
          console.log('[UPB]', value);
          result = { printed: value };
          break;
        }
        
        case 'log': {
          const message = this.resolveValue(this.getNodeParameter('message', 0), variables);
          const level = this.getNodeParameter('logLevel', 0);
          console[level]('[UPB]', message);
          result = { logged: message, level };
          break;
        }
        
        default:
          result = { message: `Operation ${operation} not implemented` };
      }
      
      // Сохраняем переменные
      this.setWorkflowStaticData('global', variables);
      
      // Закрываем браузер
      if (browser) await browser.close();
      
      const saveTo = this.getNodeParameter('saveTo', 0);
      if (saveTo && result !== null) {
        return [{ json: { [saveTo]: result, operation } }];
      }
      return [{ json: { result, operation } }];
      
    } catch (error: any) {
      if (browser) await browser.close();
      throw new Error(`UPBParser error: ${error.message}`);
    }
  }
  
  private resolveValue(value: any, variables: Record<string, any>): any {
    if (typeof value === 'string' && value.match(/{{.*}}/)) {
      const varName = value.slice(2, -2).trim();
      return variables[varName] !== undefined ? variables[varName] : value;
    }
    return value;
  }
}