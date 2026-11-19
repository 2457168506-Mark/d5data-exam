package com.example.helloworld.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Spring Security 安全配置。
 *
 * <p>定义三件事:
 * <ol>
 *   <li>安全规则链:所有请求必须登录,未登录自动 302 到内置登录页 /login;</li>
 *   <li>内存用户账号:test / 123456,BCrypt 加密存储;</li>
 *   <li>密码加密器:BCryptPasswordEncoder(慢哈希 + 自动加盐,抗暴力破解)。</li>
 * </ol>
 *
 * <p>认证方式为会话 Cookie(JSESSIONID),无 JWT 等额外复杂度。
 */
@Configuration
public class SecurityConfig {

    /**
     * 安全过滤器链。
     *
     * <p>每一条进入应用的 HTTP 请求都会先经过这条链上的各个 Filter,
     * 由它们判断"是否需要登录 / 是否已登录 / 是否有权限"。
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 关闭 CSRF 防护:CSRF 主要针对浏览器表单场景,本题为纯 API 演示(curl 调用),
            // 不依赖 Cookie 自动提交表单的行为,故关闭以简化测试。
            .csrf(csrf -> csrf.disable())

            // 授权规则:所有请求都需要认证。
            // 未登录访问任意接口(如 /hello)会被 Spring Security 的认证入口拦截,
            // 返回 302 重定向到 /login(由下面的 formLogin 提供的默认登录页)。
            .authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated()
            )

            // 启用 Spring Security 内置的表单登录。
            // GET /login  -> 框架自动生成登录页(一个标准 HTML 表单)
            // POST /login -> 框架内置过滤器校验 username/password,
            //              校验通过后把用户信息放进服务端 Session,
            //              并给浏览器下发 JSESSIONID Cookie 作为后续请求的通行证。
            .formLogin(Customizer.withDefaults());

        return http.build();
    }

    /**
     * 用户详情服务:负责告诉 Spring Security "系统里有哪些账号"。
     *
     * <p>这里用 InMemoryUserDetailsManager 把唯一账号存在内存里,
     * 重启应用账号就重置——对笔试演示足够,真实项目应改造成从数据库加载。
     */
    @Bean
    public UserDetailsService userDetailsService(PasswordEncoder passwordEncoder) {
        var user = User.builder()
            .username("test")                          // 用户名
            .password(passwordEncoder.encode("123456")) // 密码经 BCrypt 加密后存入,登录时比对密文
            .roles("USER")                              // 角色,用于后续细粒度权限控制(本题未用到)
            .build();
        return new InMemoryUserDetailsManager(user);
    }

    /**
     * 密码加密器:采用 BCrypt 算法。
     *
     * <p>不同于 MD5/SHA 等快速哈希,BCrypt 专为密码设计:
     * 慢哈希(GPU 暴力破解成本高)+ 自动加盐(每次加密同一密码结果不同)。
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
