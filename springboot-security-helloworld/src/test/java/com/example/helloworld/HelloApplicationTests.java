package com.example.helloworld;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 集成测试类:启动完整 Spring 容器(包括 SecurityFilterChain),
 * 用 MockMvc 在不启动真实 Tomcat 的情况下模拟 HTTP 请求,
 * 验证"未登录被拦截 → 登录 → 访问受保护接口"这条完整链路。
 *
 * <p>测试在 mvn test / mvn package 时自动执行,全部通过才允许生成 jar。
 */
@SpringBootTest              // 启动 Spring 容器(加载 HelloApplication 的全部组件)
@AutoConfigureMockMvc        // 自动注入 MockMvc(模拟浏览器发请求,不走真实网络)
class HelloApplicationTests {

    @Autowired
    private MockMvc mockMvc;  // Spring 提供的"模拟浏览器",可执行 get/post 并断言响应

    /** 容器能正常加载——最基础的冒烟测试。 */
    @Test
    void contextLoads() {
    }

    /** 未登录直接访问 /hello → 应被 Spring Security 302 重定向到登录页。 */
    @Test
    void helloWithoutLoginRedirectsToLoginPage() throws Exception {
        mockMvc.perform(get("/hello"))
            .andExpect(status().is3xxRedirection())            // 30x 系列重定向
            .andExpect(redirectedUrl("http://localhost/login")); // 目标地址是内置登录页
    }

    /** 登录页本身无需认证,直接 GET 应返回 200(HTML 表单)。 */
    @Test
    void loginPageIsAccessible() throws Exception {
        mockMvc.perform(get("/login"))
            .andExpect(status().isOk());
    }

    /** 密码错误 → Spring Security 认证失败,重定向到 /login?error(登录页会显示错误提示)。 */
    @Test
    void loginWithWrongPasswordFails() throws Exception {
        mockMvc.perform(post("/login")
                .param("username", "test")
                .param("password", "wrong"))
            .andExpect(status().is3xxRedirection())
            .andExpect(redirectedUrl("/login?error"));
    }

    /**
     * 正确登录后,同一会话内访问 /hello → 返回 "Hello World"。
     *
     * <p>MockMvc 不启动真实 Tomcat,因此不会像真实浏览器那样自动把 JSESSIONID 回写为 Cookie,
     * 这里手动从登录请求中取出服务端创建的 Session 对象,传给后续请求——
     * 本质上是验证"认证状态确实存在于服务端 Session 里"。
     */
    @Test
    void loginThenAccessHelloWithinSameSession() throws Exception {
        // 第一步:正确密码登录,Spring Security 会在服务端内存中创建 Session
        MvcResult login = mockMvc.perform(post("/login")
                .param("username", "test")
                .param("password", "123456"))
            .andExpect(status().is3xxRedirection())
            .andReturn();

        // 从登录请求的上下文中拿到刚创建的 Session(未登录时为 null,
        // 所以用 getSession(false)——不主动创建,只取已有的)
        MockHttpSession session = (MockHttpSession) login.getRequest().getSession(false);

        // 第二步:带着同一个 Session 访问受保护接口 → 认证通过,返回 Hello World
        String body = mockMvc.perform(get("/hello").session(session))
            .andExpect(status().isOk())
            .andReturn().getResponse().getContentAsString();

        assertThat(body).isEqualTo("Hello World");
    }
}
