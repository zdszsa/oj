package com.zzh.oj.common;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

/**
 * 通用分页结果
 */
@Data
@AllArgsConstructor
public class PageResult<T> {

    /** 总条数（前端算总页数用） */
    private long total;

    /** 当前第几页，从 1 开始 */
    private int page;

    /** 每页多少条 */
    private int size;

    private List<T> list;
}
