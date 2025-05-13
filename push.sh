#!/bin/bash
# ����Ϊ push.sh�����ִ��Ȩ�޺�ʹ�ã�chmod +x push.sh && ./push.sh

# �������� (�����޸�)
REMOTE1="github"    # ��һ��Զ�ֿ̲����� (�� GitHub)
REMOTE2="origin"    # �ڶ���Զ�ֿ̲����� (�� Gitee)
BRANCH="master"     # Ҫ���͵ķ�֧����

# ��ɫ������ʾ
echo -e "\033[31m??  ���棺ǿ�����ͻḲ��Զ�ֿ̲���ʷ��¼��\033[0m"
read -p "ȷ��Ҫǿ��������(y/N) " -n 1 -r
echo    # ����
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# ǿ�����͵���һ���ֿ�
git push --force $REMOTE1 $BRANCH

# ���͵��ڶ����ֿⲢ��������
git push -u $REMOTE2 $BRANCH

echo "������ɣ�"