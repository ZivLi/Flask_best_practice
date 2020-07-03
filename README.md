## <u>代码提交流程</u> 

1. 从 [远端代码库](https://gitlab.ainnovation.com/orion/fox)  Fork 一份到 auth（本人） 的 repo

2. 在本地 clone 代码并添加远端库

   ```shell
   > git clone https://gitlab.ainnovation.com/<auth>/fox.git
   > git remote add upstream https://gitlab.ainnovation.com/mli-algo/fox.git
   	# 查看配置的远端库
   > git remote -v
   	# git 默认使用origin来标识你所克隆的原始仓库
     origin	https://gitlab.ainnovation.com/<auth>/fox.git (fetch)
     origin	https://gitlab.ainnovation.com/<auth>/fox.git (push)
     upstream	https://gitlab.ainnovation.com/mli-algo/fox.git (fetch)
     upstream	https://gitlab.ainnovation.com/mli-algo/fox.git (push)
   ```

3. 新需求（card）开发之前必须首先 rebase upstream develop分支，然后 checkout 新的需求分支，以 Feature- 开头，简述 card 内容建立分支

   ```shell
   > git checkout (-b) develop
   > git pull --rebase upstream develop
   > git checkout -b Feature-card-target
   ```

4. card 开发流程严格按照拆分检查项（tasks）进行，每完成一个 task，进行一次原子性 commit，提交信息简单明确提交所含内容。

   ```shell
   > git add <modified files>
   > git commit -m 'commit message'
   ```

   需要注意的是，如果有对数据库的修改，单独的 model 修改和生成对应的 migration files需要第一时间单独提交，保证连接开发环境数据库的其他 member 数据访问不会受到影响。

5. card 开发完成后，先要把远端 develop 分支同步到本地，解决冲突（若存在），然后提交 merge request，远端分支指定为 develop分支，通知其他 member 进行 code review，有对应的 discussion 解决完成之后，对应的 code reviewers 点击 approval。当至少有两位其他 member 对当前 merge request 进行 approvaled之后，@管理员进行 merge 操作。补充 merge request 链接到 kanban。并迁移 card 进行状态。

   ```shell
   > git checkout develop
   > git pull --rebase upstream develop
   > git checkout Feature-card-target
   > git merge develop
   > git push origin Feature-card-target
   ```

6. 测试环境经测试人员测试通过后，从远端 develop 分支切出单独迭代版本的 release-v1.0 分支，向 master 分支提merge request，待发布到生产正式环境。
7. 当需要进行生产正式环境的 Hotfix 时，从远端 rebase master分支，checkout 新的hotfix 分支。以 Hotfix- 开头，简述修复内容。待正式环境 bug 修复后，再把 Hotfix 的内容，同步到远端 develop分支中。

## <u>后端项目部署</u>

### 【_开发环境_】

在本地开发环境安装项目依赖包

```shell
> pip install -r requirements.txt
```

增加 git pre-push hook

```shell
> cd scripts
> chmod +x add-pre-push-hook.sh
> ./add-pre-push-hook.sh
```

在项目根目录下执行

```shell
> python app_main.py runserver
```

访问 [本地测试端口](http://127.0.0.1:5000/demo?test=1) ，正常返回 "ok"，则表示后端服务运行正常。

本地执行 celery 任务

```shell
> celery worker -A celery_tasks.celery_init.celery --loglevel=INFO
```



### 【_测试环境_】

检查开发环境docker（19.03.5）版本。[参考文档](https://www.docker.com/)

```shel
> docker --version
```



## <u>数据库修改操作流程</u>

在本地对 db.model 对象进行修改（增加 model， 修改 model 字段属性，删除 model 字段等操作），然后执行

```shell
> python app_main.py db migrate -m 'modify fields message'
```

检查生成在对应 migrations/versions/ 文件夹下的 migration文件 alembic_verion.py 内容，确认文件执行内容无误，提交当前 model 修改和生成的 migrations/versions/alembic_version.py 文件，创建MR。

MR 被 merge 之后，在本地执行 upgrade 操作

```shell
> python app_main.py db upgrade
```

执行完成后，检查对应数据库/表中，结构是否发生正确变化。

## <u>wiki 接口文档提交流程</u>

1. 在本地克隆wiki接口文档

   ```shell
   > git clone https://gitlab.ainnovation.com/mli-algo/fox.wiki.git
   ```

2. 进入Aiscm_apis目录下，修改相应的接口文档

   ```shell
   > cd [克隆文档路径]/fox.wiki/Aiscm_apis
   ```

3. 提交修改，每次push前，需拉取最新代码，再push到远端master分支上

   ```shell
   > git status
   > git add <modified files>
   > git commit -m "commit message"
   > git pull origin master
   # 如有冲突，需解决冲突后再push
   > git push origin master
   ```

4. 如需新建接口文档，需要在Aiscm_apis目录下新增后缀.md的文件
5. push成功后在[远端项目](https://gitlab.ainnovation.com/mli-algo/fox/wikis/Aiscm_apis/api_doc)查看wiki是否更新成功



 ---Authors: ZivLi, Wanghonggang, Sunhongxiang, Mumu
