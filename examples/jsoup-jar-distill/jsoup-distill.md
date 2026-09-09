# jsoup API 速查（基于 1.17.2 反编译源码）

## 一、核心入口

### 1. Jsoup.parse（解析 HTML）
```java
// 解析字符串（Jsoup）
Document doc = Jsoup.parse(String html);                    // 无 baseUri
Document doc = Jsoup.parse(String html, String baseUri);   // 指定 baseUri
Document doc = Jsoup.parse(String html, String baseUri, Parser parser); // 自定义解析器

// 解析文件（Jsoup）
Document doc = Jsoup.parse(File in, String charsetName);   // 自动使用文件绝对路径作 baseUri
Document doc = Jsoup.parse(File in, String charsetName, String baseUri);

// 解析输入流（Jsoup）
Document doc = Jsoup.parse(InputStream in, String charsetName, String baseUri);

// 解析 body 片段（Jsoup）
Document doc = Jsoup.parseBodyFragment(String bodyHtml);   // 返回完整 Document，内容在 body()
```

### 2. Jsoup.connect（HTTP 连接）
```java
Connection con = Jsoup.connect(String url);   // 返回 Connection 接口
Document doc = con.get();                     // GET 请求（Connection）
Document doc = con.post();                    // POST 请求（Connection）
Response res = con.execute();                 // 执行请求（Connection）
```

**Connection 链式配置**（均返回 Connection，可链式调用）：
```java
con.url(String url)          // 设置 URL
con.userAgent(String)        // 设置 User-Agent
con.timeout(int millis)      // 超时时间
con.maxBodySize(int bytes)   // 最大响应体大小
con.followRedirects(boolean) // 是否跟随重定向
con.ignoreHttpErrors(boolean)// 忽略 HTTP 错误状态码
con.ignoreContentType(boolean) // 忽略 Content-Type 校验
con.method(Method.POST)      // 设置请求方法（Connection.Method 枚举）
con.header(String, String)   // 设置请求头
con.cookie(String, String)   // 设置 Cookie
con.data(String key, String value) // 添加表单数据
con.requestBody(String)      // 设置请求体
con.parser(Parser)           // 自定义解析器
```

**Response 常用方法**（Connection.Response）：
```java
res.statusCode()       // 状态码
res.statusMessage()    // 状态消息
res.contentType()      // Content-Type
res.body()             // 响应体字符串
res.bodyAsBytes()      // 响应体字节数组
res.parse()            // 解析为 Document
res.charset()          // 获取字符集
```

**Connection.Method 枚举**：GET(false), POST(true), PUT(true), DELETE(true), PATCH(true), HEAD(false), OPTIONS(false), TRACE(false)。`hasBody()` 返回是否带请求体。

### 3. Jsoup.newSession()
```java
Connection session = Jsoup.newSession();  // 创建新会话，可复用 Cookie 等状态
```

## 二、元素选择

### 1. CSS 选择器（Element）
```java
Elements els = element.select(String cssQuery);   // 选择所有匹配元素
Element el = element.selectFirst(String cssQuery); // 选择第一个匹配元素
Element el = element.expectFirst(String cssQuery); // 选择第一个，无匹配抛异常
boolean isMatch = element.is(String cssQuery);     // 判断元素是否匹配
Element closest = element.closest(String cssQuery); // 向上查找最近的匹配祖先
```

### 2. 遍历方法（Element）
```java
Elements children = element.children();       // 直接子元素
Element child = element.child(int index);     // 第 index 个子元素
int count = element.childrenSize();           // 子元素数量
Element parent = element.parent();            // 父元素
Elements parents = element.parents();         // 所有祖先元素
Element firstChild = element.firstElementChild();  // 第一个子元素
Element lastChild = element.lastElementChild();    // 最后一个子元素
Element prevSib = element.previousElementSibling(); // 前一个兄弟元素
Element nextSib = element.nextElementSibling();     // 后一个兄弟元素
Elements siblings = element.siblingElements();      // 所有兄弟元素
int idx = element.elementSiblingIndex();            // 兄弟元素索引
```

### 3. 按属性/标签查找（Element）
```java
Elements byTag = element.getElementsByTag(String tagName);
Element byId = element.getElementById(String id);
Elements byClass = element.getElementsByClass(String className);
Elements byAttr = element.getElementsByAttribute(String key);
Elements byAttrVal = element.getElementsByAttributeValue(String key, String value);
Elements all = element.getAllElements();
```

### 4. Elements 集合操作（Elements）
```java
Element first = els.first();    // 第一个元素，空则 null
Element last = els.last();      // 最后一个元素，空则 null
Elements filtered = els.select(String query);  // 在结果中继续选择
Elements not = els.not(String query);          // 排除匹配的元素
Elements eq = els.eq(int index);               // 取第 index 个元素
boolean anyMatch = els.is(String query);       // 是否有元素匹配
Elements nextAll = els.nextAll();              // 所有后续兄弟
Elements prevAll = els.prevAll();              // 所有前驱兄弟
Elements parents = els.parents();              // 所有元素的祖先集合
```

## 三、DOM 读写

### 1. 文本操作（Element）
```java
String text = element.text();        // 获取规范化文本（合并空白）
element.text(String text);           // 设置文本内容（替换原有内容）
String ownText = element.ownText();  // 仅直接文本子节点
String wholeText = element.wholeText(); // 保留原始空白
boolean hasText = element.hasText(); // 是否包含非空白文本
```

### 2. HTML 操作（Element）
```java
String html = element.html();        // 获取内部 HTML
element.html(String html);           // 设置内部 HTML（替换内容）
String outerHtml = element.outerHtml(); // 获取包含自身的 HTML
element.append(String html);         // 内部末尾追加 HTML
element.prepend(String html);        // 内部开头插入 HTML
element.before(String html);         // 在元素前插入
element.after(String html);          // 在元素后插入
element.empty();                     // 清空子节点
element.remove();                    // 从 DOM 中移除自身
element.wrap(String html);           // 用 HTML 包裹元素
```

### 3. 子节点操作（Element）
```java
element.appendChild(Node child);     // 追加子节点
element.prependChild(Node child);    // 头部插入子节点
element.appendElement(String tagName); // 创建并追加新元素
element.prependElement(String tagName); // 创建并头部插入新元素
element.appendText(String text);     // 追加文本节点
element.insertChildren(int index, Node... children); // 指定位置插入
```

### 4. 属性操作（Element/Node）
```java
String val = element.attr(String key);      // 获取属性值
element.attr(String key, String value);     // 设置属性
element.attr(String key, boolean value);    // 设置布尔属性
boolean has = element.hasAttr(String key);  // 是否有属性
element.removeAttr(String key);             // 移除属性
Attributes attrs = element.attributes();    // 获取所有属性
Map<String, String> dataset = element.dataset(); // 获取 data-* 属性
String absUrl = element.absUrl(String key); // 解析为绝对 URL
```

### 5. 类名操作（Element）
```java
element.addClass(String className);
element.removeClass(String className);
element.toggleClass(String className);
boolean has = element.hasClass(String className);
Set<String> classes = element.classNames();
element.classNames(Set<String> classes);
```

### 6. 表单值（Element）
```java
String val = element.val();   // 获取 value 属性（textarea 返回文本）
element.val(String value);    // 设置 value
```

### 7. Document 特有方法（Document）
```java
Element body = doc.body();        // body 元素
Element head = doc.head();        // head 元素
String title = doc.title();       // 获取 title
doc.title(String title);          // 设置 title
String location = doc.location(); // 文档 URL
List<FormElement> forms = doc.forms(); // 所有表单
FormElement form = doc.expectForm(String cssQuery); // 查找表单，无则抛异常
doc.charset(Charset charset);     // 设置字符集
doc.outputSettings(OutputSettings); // 设置输出选项
doc.parser(Parser parser);        // 设置解析器
```

### 8. 输出设置（Document.OutputSettings）
```java
Document.OutputSettings settings = doc.outputSettings();
settings.prettyPrint(boolean);    // 是否格式化输出
settings.syntax(Syntax.html/xml); // 输出语法
settings.charset(String charset); // 字符集
settings.escapeMode(EscapeMode);  // 转义模式
settings.indentAmount(int);       // 缩进量
```

## 四、HTML 清洗（Safelist）

### 1. 预定义 Safelist（Safelist）
```java
Safelist none = Safelist.none();              // 不允许任何标签
Safelist simple = Safelist.simpleText();      // 仅 b, em, i, strong, u
Safelist basic = Safelist.basic();            // 基础 HTML（a, p, ul 等）
Safelist basicImages = Safelist.basicWithImages(); // basic + img
Safelist relaxed = Safelist.relaxed();        // 宽松（含 table, div 等）
```

### 2. 清洗方法（Jsoup）
```java
String cleanHtml = Jsoup.clean(String bodyHtml, Safelist safelist);
String cleanHtml = Jsoup.clean(String bodyHtml, String baseUri, Safelist safelist);
boolean isValid = Jsoup.isValid(String bodyHtml, Safelist safelist);
```

### 3. 自定义 Safelist（Safelist）
```java
Safelist safelist = new Safelist();
safelist.addTags(String... tags);              // 允许标签
safelist.removeTags(String... tags);           // 移除标签
safelist.addAttributes(String tag, String... attrs); // 允许属性
safelist.removeAttributes(String tag, String... attrs);
safelist.addEnforcedAttribute(String tag, String attr, String value); // 强制属性
safelist.removeEnforcedAttribute(String tag, String attr);
safelist.addProtocols(String tag, String attr, String... protocols); // 允许协议
safelist.removeProtocols(String tag, String attr, String... protocols);
safelist.preserveRelativeLinks(boolean);       // 保留相对链接
```

**注意**：`addTags("noscript")` 会抛异常（源码中明确禁止）。

## 五、高频方法速查表

| 操作 | 方法 | 出处 |
|------|------|------|
| 解析 HTML 字符串 | `Jsoup.parse(String)` | Jsoup |
| 解析 body 片段 | `Jsoup.parseBodyFragment(String)` | Jsoup |
| 建立连接 | `Jsoup.connect(String)` | Jsoup |
| 执行 GET | `Connection.get()` | Connection |
| 执行 POST | `Connection.post()` | Connection |
| 获取响应体 | `Response.body()` | Connection.Response |
| CSS 选择 | `Element.select(String)` | Element |
| 选择第一个 | `Element.selectFirst(String)` | Element |
| 获取文本 | `Element.text()` | Element |
| 设置文本 | `Element.text(String)` | Element |
| 获取 HTML | `Element.html()` | Element |
| 设置 HTML | `Element.html(String)` | Element |
| 追加 HTML | `Element.append(String)` | Element |
| 获取属性 | `Element.attr(String)` | Element |
| 设置属性 | `Element.attr(String, String)` | Element |
| 移除属性 | `Element.removeAttr(String)` | Element |
| 添加类 | `Element.addClass(String)` | Element |
| 移除类 | `Element.removeClass(String)` | Element |
| 判断类 | `Element.hasClass(String)` | Element |
| 获取值 | `Element.val()` | Element |
| 获取子元素 | `Element.children()` | Element |
| 获取父元素 | `Element.parent()` | Element |
| 获取 body | `Document.body()` | Document |
| 获取 title | `Document.title()` | Document |
| 清洗 HTML | `Jsoup.clean(String, Safelist)` | Jsoup |
| 验证 HTML | `Jsoup.isValid(String, Safelist)` | Jsoup |
| 创建 Safelist | `Safelist.basic()` | Safelist |
| 添加标签 | `Safelist.addTags(String...)` | Safelist |
| 添加属性 | `Safelist.addAttributes(String, String...)` | Safelist |
| 添加协议 | `Safelist.addProtocols(String, String, String...)` | Safelist |

**实现细节未在材料中**：`Connection.auth()` 默认抛 `UnsupportedOperationException`；`Document.connection()` 在无连接时返回 `Jsoup.newSession()`。