package com.zzh.oj.mapper;

import com.zzh.oj.dto.SubmissionDetailVO;
import com.zzh.oj.dto.SubmissionVO;
import com.zzh.oj.entity.Submission;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface SubmissionMapper {

    /** 插入一条提交记录，回填自增 id */
    int insert(Submission submission);

    /** 按 id 查（列表页字段） */
    Submission selectById(Long id);

    /** 某用户一共多少条提交 */
    long countByUserId(@Param("userId") Long userId);

    /** 某用户的提交记录（连表带出题目标题），按时间倒序分页 */
    List<SubmissionVO> selectVOByUserId(@Param("userId") Long userId,
                                        @Param("offset") int offset,
                                        @Param("limit") int limit);

    /** 某题的所有提交，按时间倒序分页 */
    List<Submission> selectByProblemId(@Param("problemId") Long problemId,
                                       @Param("offset") int offset,
                                       @Param("limit") int limit);

    /** 提交详情：连表带出题目标题，再带上代码和判题输出 */
    SubmissionDetailVO selectDetailById(@Param("id") Long id);

    /** 更新判题结果 */
    int updateStatus(@Param("id") Long id,
                     @Param("status") Integer status,
                     @Param("timeMs") Integer timeMs);
}
