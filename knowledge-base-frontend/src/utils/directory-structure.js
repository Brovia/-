/**
 * 云厂商目录结构配置
 * 定义云厂商和产品分类的层级关系
 */

// 云厂商配置
export const CLOUD_PROVIDERS = {
  '腾讯云': {
    name: '腾讯云',
    icon: 'tencent',
    color: '#006EFF',
    products: [
      '负载均衡 CLB',
      '私有网络 VPC', 
      '弹性IP',
      'NAT网关',
      '专线接入',
      '云联网',
      'VPN连接',
      '云防火墙',
      'DDoS防护',
      'Web应用防火墙'
    ]
  },
  '阿里云': {
    name: '阿里云',
    icon: 'aliyun',
    color: '#FF6A00',
    products: [
      '传统型负载均衡 CLB',
      '应用型负载均衡 ALB',
      '网络型负载均衡 NLB',
      '专有网络 VPC',
      '弹性公网IP',
      'NAT网关',
      '专线接入',
      '云企业网',
      'VPN网关',
      '云防火墙'
    ]
  },
  '火山云': {
    name: '火山云',
    icon: 'volcano',
    color: '#FF4D4F',
    products: [
      '负载均衡',
      '私有网络',
      '弹性公网IP',
      'NAT网关',
      '专线连接',
      '云联网',
      'VPN连接'
    ]
  },
  '华为云': {
    name: '华为云',
    icon: 'huawei',
    color: '#FF6900',
    products: [
      '弹性负载均衡 ELB',
      '虚拟私有云 VPC',
      '弹性公网IP',
      'NAT网关',
      '云专线',
      '云连接',
      'VPN连接'
    ]
  },
  'AWS': {
    name: 'AWS',
    icon: 'aws',
    color: '#FF9900',
    products: [
      'Application Load Balancer',
      'Network Load Balancer',
      'Classic Load Balancer',
      'VPC',
      'Elastic IP',
      'NAT Gateway',
      'Direct Connect',
      'Transit Gateway',
      'VPN Connection'
    ]
  },
  'Azure': {
    name: 'Azure',
    icon: 'azure',
    color: '#0078D4',
    products: [
      'Application Gateway',
      'Load Balancer',
      'Virtual Network',
      'Public IP',
      'NAT Gateway',
      'ExpressRoute',
      'Virtual WAN',
      'VPN Gateway'
    ]
  },
  'GCP': {
    name: 'GCP',
    icon: 'gcp',
    color: '#4285F4',
    products: [
      'Cloud Load Balancing',
      'VPC',
      'External IP',
      'Cloud NAT',
      'Cloud Interconnect',
      'Cloud VPN'
    ]
  }
}

// 产品分类配置
export const PRODUCT_CATEGORIES = {
  '负载均衡': {
    name: '负载均衡',
    description: '分发网络流量，提高应用可用性',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  '私有网络': {
    name: '私有网络',
    description: '构建隔离的虚拟网络环境',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  '弹性IP': {
    name: '弹性IP',
    description: '静态公网IP地址管理',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  'NAT网关': {
    name: 'NAT网关',
    description: '网络地址转换服务',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  '专线': {
    name: '专线',
    description: '高速稳定的专线连接',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  '云联网': {
    name: '云联网',
    description: '多地域网络互联',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  },
  'VPN': {
    name: 'VPN',
    description: '虚拟专用网络连接',
    providers: ['腾讯云', '阿里云', '火山云', '华为云', 'AWS', 'Azure', 'GCP']
  }
}

// 生成目录树结构
export const generateDirectoryTree = () => {
  const tree = []
  
  Object.entries(CLOUD_PROVIDERS).forEach(([providerKey, provider]) => {
    const providerNode = {
      id: `provider-${providerKey}`,
      type: 'provider',
      name: provider.name,
      icon: provider.icon,
      color: provider.color,
      children: [],
      expanded: false
    }
    
    // 为每个产品创建目录
    provider.products.forEach(product => {
      const productNode = {
        id: `product-${providerKey}-${product}`,
        type: 'product',
        name: product,
        parent: providerKey,
        children: [],
        expanded: false
      }
      providerNode.children.push(productNode)
    })
    
    tree.push(providerNode)
  })
  
  return tree
}

// 获取云厂商信息
export const getProviderInfo = (providerName) => {
  return CLOUD_PROVIDERS[providerName] || null
}

// 获取产品分类信息
export const getCategoryInfo = (categoryName) => {
  return PRODUCT_CATEGORIES[categoryName] || null
}

// 根据文档信息确定目录路径
export const getDocumentPath = (document) => {
  const provider = document.provider
  const category = document.category
  
  if (!provider || !category) {
    return ['未分类']
  }
  
  return [provider, category]
}

// 检查文档是否属于指定目录
export const isDocumentInDirectory = (document, directoryPath) => {
  const docPath = getDocumentPath(document)
  
  if (directoryPath.length === 1) {
    // 云厂商级别
    return docPath[0] === directoryPath[0]
  } else if (directoryPath.length === 2) {
    // 产品级别
    return docPath[0] === directoryPath[0] && docPath[1] === directoryPath[1]
  }
  
  return false
}
