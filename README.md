# NCCU_Project

-- MySQL安裝  
https://clay-atlas.com/blog/2019/11/16/mysql-mysqlworkbench-tutorial-download-install-steps/  
  
-- 連線及建立SCHEMA  
https://ithelp.ithome.com.tw/articles/10215161  
  
建立完SCHEMA後即可執行Google Drive上的CREATE TABLE.sql, TABLE建立成功執行INSERT DATA.sql  
  
目前的SCHEMA名稱: nccu_project  
UserName: root  
Password: 1234  
(照這個設定才不需改Django project裡的settings)  
  
  
-- 從git上clone程式碼  
Step.1  
新建虛擬環境 & 切換至虛擬環境  
(https://djangogirlstaipei.gitbooks.io/django-girls-taipei-tutorial/content/django/installation.html)  
  
Step.2  
從git上clone下程式碼  
** 注意clone時要選擇master分支  
clone網址: https://github.com/squirrelnrosie/NCCU-Project.git  
  
Step.3  
安裝所需套件  
- cd 至 requirement.txt所在位置(NCCU-Project)  
- cmd下指令: pip install -r requirements.txt  
  
以上步驟完成後即可測試專案是否能成功執行

--- 資料庫更動紀錄(script請至Google Drive拿取  
201211 1. 針對現金Ans-v.3做的修改於資料表Depositaccount新增欄位Type  
       2. 新增科目
